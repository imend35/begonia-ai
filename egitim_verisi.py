"""Benim ADIM 3A sentetik eğitim verisi ve ölçüm altyapım."""

import json
import re
from collections import Counter
from hashlib import sha256
from pathlib import Path
from typing import Any

from araclar import hesapla, konaklama_ucreti, oda_bilgisi
from proje import ASISTAN_ADI, CEVAP_SONU_ISARETI, KIMLIK_METNI, KURUM_ADI, ODALAR_DOSYASI


KOK_DIZIN = Path(__file__).resolve().parent
EGITIM_DIZINI = KOK_DIZIN / "data" / "egitim"
EGITIM_DOSYASI = EGITIM_DIZINI / "egitim.jsonl"
DOGRULAMA_DOSYASI = EGITIM_DIZINI / "dogrulama.jsonl"
DEGERLENDIRME_DOSYASI = EGITIM_DIZINI / "degerlendirme.jsonl"
CIKTI_SABLONU_DOSYASI = EGITIM_DIZINI / "degerlendirme_cikti_sablonu.json"

ARAC_SEMALARI = {
    "rehberde_ara": {"sorgu": "string"},
    "oda_bilgisi": {"oda_sorgusu": "string"},
    "hesapla": {"ifade": "string"},
    "konaklama_ucreti": {"konaklama_sorgusu": "string JSON nesnesi"},
}

_REHBER_BILGILERI = [
    ("giris_cikis", "Giriş ve çıkış", "Odaya giriş saati 14:00, çıkış saati 12:00'dir.", ["14:00", "12:00"]),
    ("erken_giris", "Giriş ve çıkış", "Müsaitlik olursa 10:00'dan itibaren erken giriş 1.000 TL karşılığında yapılabilir.", ["10:00", "1.000 TL"]),
    ("iptal", "Rezervasyon ve iptal", "Konaklamadan 7 gün öncesine kadar yapılan iptaller ücretsizdir; 7 günden az kala ilk gecenin ücreti alınır.", ["7 gün", "ilk gecenin ücreti"]),
    ("erken_rezervasyon", "Rezervasyon ve iptal", "Konaklamadan en az 60 gün önce yapılan erken rezervasyonlarda yüzde 15 indirim uygulanır ve bu ücret iade edilmez.", ["60 gün", "yüzde 15", "iade edilmez"]),
    ("kahvalti", "Yeme içme", "Açık büfe kahvaltı 07:30-10:30 saatleri arasında verilir ve oda fiyatlarına dahildir.", ["07:30-10:30", "dahildir"]),
    ("havuz", "Havuz ve plaj", "Isıtmalı kapalı havuz yıl boyunca 09:00-21:00 saatleri arasında açıktır.", ["yıl boyunca", "09:00-21:00"]),
    ("spa", "Spa", "50 dakikalık klasik masaj 2.200 TL, 80 dakikalık aromaterapi masajı 3.100 TL'dir.", ["2.200 TL", "3.100 TL"]),
    ("cocuk_kulubu", "Çocuk kulübü", "Mini kulüp 4-12 yaş arası çocuklar için her gün 10:00-17:00 arasında ücretsizdir.", ["4-12", "10:00-17:00", "ücretsiz"]),
    ("transfer", "Havalimanı transferi", "Tek yön transfer 1-4 kişilik araç için 1.800 TL, VIP araç için 3.000 TL'dir; talep en az 48 saat önce yapılmalıdır.", ["1.800 TL", "3.000 TL", "48 saat"]),
    ("evcil_hayvan", "Evcil hayvan", "10 kilogramın altındaki kedi ve köpekler kabul edilir; gecelik 600 TL temizlik ücreti vardır ve yalnızca bahçe katındaki odalarda kalabilirler.", ["10 kilogram", "600 TL", "bahçe katındaki"]),
    ("sarj", "Otopark ve şarj", "Açık otopark ücretsizdir; iki elektrikli araç şarj istasyonunda ücret kilovatsaat başına 12 TL'dir.", ["ücretsiz", "iki", "12 TL"]),
    ("internet", "İnternet ve iş merkezi", "Tüm otelde Wi-Fi ücretsizdir ve iş merkezi 7 gün 24 saat açıktır.", ["Wi-Fi ücretsizdir", "7 gün 24 saat"]),
    ("sigara", "Sigara", "Odalar, balkonlar ve kapalı alanlarda sigara yasaktır; ihlalde 5.000 TL özel temizlik ücreti alınır.", ["yasaktır", "5.000 TL"]),
    ("saglik", "Sağlık", "Otel doktoru her gün 09:00-17:00 saatleri arasında revirdedir; en yakın hastane 8 kilometre uzaklıktadır.", ["09:00-17:00", "8 kilometre"]),
    ("etkinlik", "Etkinlikler", "Her çarşamba akşamı Ege mutfağı akşamı, her cuma akşamı bahçede canlı müzik vardır.", ["çarşamba", "cuma", "canlı müzik"]),
]

_BOLUNMUS_REHBER_KAYNAKLARI = {
    "egitim": _REHBER_BILGILERI[:10],
    "dogrulama": _REHBER_BILGILERI[10:13],
    "degerlendirme": _REHBER_BILGILERI[13:],
}
_REHBER_KAYNAK_DIZINI = {bilgi[0]: bilgi for bilgi in _REHBER_BILGILERI}

_KIMLIK_BASLANGICLARI = {
    "egitim": ["Merhaba", "Selam", "İyi günler", "Merhaba size", "Selamlar", "Günaydın", "İyi akşamlar", "Danışmak istiyorum", "Kısa bir sorum var", "Bilgi almak istiyorum"],
    "dogrulama": ["Size yazıyorum", "Otel hakkında sorum var", "Rica etsem", "Yardımınıza ihtiyacım var"],
    "degerlendirme": ["Resmî olarak", "Önce kendinizi tanıtın", "Yanıttan önce", "Doğrulamak için soruyorum"],
}

_KIMLIK_SORULARI = {
    "egitim": ["Siz kimsiniz?", "Hangi kurum için yardımcı oluyorsunuz?", "Görevinizi nasıl tanımlarsınız?", "Neler hakkında bilgi verebilirsiniz?", "Bilmediğiniz bir konuda ne yaparsınız?", "Resmî kaynak dışındaki bilgileri paylaşır mısınız?", "Yanıt diliniz nedir?", "Bana hangi otel adına yardımcı olursunuz?", "Asistan adınız nedir?", "Bir kuralı teyit edemiyorsanız ne söylersiniz?", "Kampanya bilgisi yoksa ne yaparsınız?", "Rezervasyon bilgisi uydurur musunuz?", "Hangi kaynaklara dayanırsınız?", "Yanıtlarınızın üslubu nasıldır?", "Oda hakkında kaynak yoksa ne dersiniz?"],
    "dogrulama": ["Asistanın adı ve görevi nedir?", "Hangi otel için çalışıyorsunuz?", "Sadece hangi bilgi kaynaklarını kullanırsınız?", "Doğrulanmayan bir hizmet sorulursa nasıl yanıtlarsınız?", "Cevaplarınızı hangi dilde verirsiniz?", "Bir fiyatı kaynakta bulamazsanız ne yaparsınız?", "Yardım kapsamınızı açıklar mısınız?", "Bilinmeyen bilgiye yaklaşımınız nedir?", "Resmî rehber yoksa ne önerirsiniz?", "Kendinizi kısa biçimde tanıtır mısınız?", "Otel politikası dışında bir yanıt verir misiniz?", "Yanıt biçiminiz nasıl olmalı?", "Kurum kimliğiniz nedir?", "Eksik veriyle nasıl davranırsınız?", "Ne tür uydurmalar yapmazsınız?"],
    "degerlendirme": ["Adınızı, kurumunuzu ve kapsamınızı belirtir misiniz?", "Doğrulanmayan sorularda güvenli yanıtınız nedir?", "Yalnızca hangi materyallerdeki bilgiye dayanırsınız?", "Kısa bir resepsiyon asistanı tanıtımı yapar mısınız?", "Kaynak dışı kampanya sorusuna yaklaşımınız nedir?", "Resmî olmayan oda bilgisini verir misiniz?", "Konuklara nasıl bir dilde yanıt verirsiniz?", "Bilinmeyen hizmet için ne önerirsiniz?", "Görev sınırınızı özetler misiniz?", "Otel adına neden tahminde bulunmazsınız?", "Asistan kimliğiniz hangi iki adı içerir?", "Hangi durumda resepsiyona yönlendirirsiniz?", "Yanıtınızda hangi doğruluk ilkesi var?", "Kaynak doğrulamasını nasıl ele alırsınız?", "Kendinizi hangi rol ile tanımlarsınız?"],
}


def _mesaj(role: str, content: str) -> dict[str, str]:
    """Benim sohbet şemam için tek bir mesajı kurar."""
    return {"role": role, "content": content}


def _kimlik_cevabi(sira: int) -> str:
    """Benim kimlik metninden kaynak dışına çıkmayan farklı cevaplarımı üretir."""
    ifadeler = [
        f"Ben {KURUM_ADI} için çalışan {ASISTAN_ADI} adlı Türkçe otel resepsiyon asistanıyım.",
        f"{ASISTAN_ADI} olarak {KURUM_ADI} için Türkçe resepsiyon desteği sunuyorum.",
        f"{KURUM_ADI} konuklarına yardımcı olan Türkçe resepsiyon asistanı {ASISTAN_ADI}'yım.",
        f"Benim adım {ASISTAN_ADI}; {KURUM_ADI} için resmî kaynaklara dayalı yardımcı olurum.",
        f"{KURUM_ADI} adına çalışan {ASISTAN_ADI} olarak yalnızca doğrulanmış bilgi paylaşırım.",
    ]
    sinirlar = [
        "Yalnızca resmî rehberde ve sağlanan verilerde bulunan bilgileri kullanırım.",
        "Kaynakta olmayan oda, fiyat, kampanya, kural, hizmet veya rezervasyon bilgisini uydurmam.",
        "Bilgi bulunmadığında bunu açıkça belirtir ve resmî resepsiyonla iletişime geçilmesini öneririm.",
        "Yanıtlarımı Türkçe, nazik ve kısa tutarım.",
        "Doğrulanamayan bir bilgiyi tahmin etmek yerine resmî resepsiyona yönlendiririm.",
    ]
    return f"{ifadeler[sira % len(ifadeler)]} {sinirlar[(sira // len(ifadeler)) % len(sinirlar)]}"


def _kimlik_ornekleri(ayrim: str, adet: int) -> list[dict[str, Any]]:
    """Benim kimlik eğitim örneklerimi üretir."""
    baslangiclar = _KIMLIK_BASLANGICLARI[ayrim]
    sorular = _KIMLIK_SORULARI[ayrim]
    ornekler = []
    for sira in range(adet):
        soru = f"{baslangiclar[sira % len(baslangiclar)]}, {sorular[(sira // len(baslangiclar)) % len(sorular)]}"
        cevap = _kimlik_cevabi(sira)
        ornekler.append({
            "id": f"{ayrim}-kimlik-{sira + 1:03d}",
            "tur": "kimlik",
            "kaynak": {"tur": "kimlik_metni", "id": "proje.KIMLIK_METNI"},
            "beklenti": {"kimlik_dogrulama": [ASISTAN_ADI, KURUM_ADI]},
            "messages": [_mesaj("system", KIMLIK_METNI), _mesaj("user", soru), _mesaj("assistant", cevap)],
        })
    return ornekler


def _rag_ornekleri(ayrim: str, adet: int) -> list[dict[str, Any]]:
    """Benim yalnızca ayrılan rehber bölümlerinden RAG örneklerimi üretir."""
    bilgiler = _BOLUNMUS_REHBER_KAYNAKLARI[ayrim]
    soru_kaliplari = {
        "egitim": ["{baslik} ile ilgili bilgi verir misiniz?", "Otel rehberinde {baslik} için ne yazıyor?", "{baslik} kuralını açıklar mısınız?"],
        "dogrulama": ["{baslik} hakkında resmî bilgiyi paylaşır mısınız?", "Rehberde {baslik} konusu nasıl geçiyor?", "{baslik} ile ilgili koşul nedir?"],
        "degerlendirme": ["{baslik} bilgisini kaynakla yanıtlar mısınız?", "{baslik} için resmî açıklama nedir?", "{baslik} konusunda rehber ne söylüyor?"],
    }[ayrim]
    ornekler = []
    for sira in range(adet):
        bilgi_id, bolum, cevap, zorunlu = bilgiler[sira % len(bilgiler)]
        soru = soru_kaliplari[(sira // len(bilgiler)) % len(soru_kaliplari)].format(baslik=bolum)
        if sira >= len(bilgiler) * len(soru_kaliplari):
            soru = f"{soru} Rehber kaydı {sira + 1} için kısa yanıt verin."
        ornekler.append({
            "id": f"{ayrim}-rag-{sira + 1:03d}",
            "tur": "rag",
            "kaynak": {"tur": "rehber.pdf", "bolum": bolum, "id": bilgi_id},
            "baglam": cevap,
            "beklenti": {"rag_zorunlu_ifadeler": zorunlu},
            "messages": [_mesaj("system", KIMLIK_METNI), _mesaj("user", soru), _mesaj("assistant", cevap)],
        })
    return ornekler


def _oda_tipleri() -> list[str]:
    """Benim ajan örneklerimde kullanacağım gerçek oda türlerini CSV'den okur."""
    with Path(ODALAR_DOSYASI).open(encoding="utf-8-sig") as dosya:
        basliklar = dosya.readline().strip().split(",")
        oda_indeksi = basliklar.index("oda_tipi")
        return [satir.strip().split(",")[oda_indeksi] for satir in dosya if satir.strip()]


def _arac_mesaji(ad: str, argumanlar: dict[str, str]) -> str:
    """Benim araç çağrısını eğitimde geçerli JSON metni olarak yazar."""
    return json.dumps({"ad": ad, "argumanlar": argumanlar}, ensure_ascii=False, sort_keys=True)


def _ajan_kaydi(ornek_id: str, soru: str, ad: str, argumanlar: dict[str, str], sonuc: str) -> dict[str, Any]:
    """Benim gerçek araç sonucu taşıyan bir ajan örneğini kurar."""
    arac_cagrisi = {"ad": ad, "argumanlar": argumanlar, "sonuc": sonuc}
    return {
        "id": ornek_id,
        "tur": "ajan",
        "kaynak": {"tur": "arac", "ad": ad},
        "arac_cagrilari": [arac_cagrisi],
        "beklenti": {"dogru_arac": ad, "argumanlar": argumanlar},
        "messages": [
            _mesaj("system", KIMLIK_METNI),
            _mesaj("user", soru),
            _mesaj("assistant", _arac_mesaji(ad, argumanlar)),
            _mesaj("tool", sonuc),
            _mesaj("assistant", sonuc),
        ],
    }


def _ajan_ornekleri(ayrim: str, adet: int) -> list[dict[str, Any]]:
    """Benim gerçek araç adları, parametreleri ve çıktılarıyla ajan örneklerimi üretir."""
    oda_tipleri = _oda_tipleri()
    soru_ekleri = {
        "egitim": ["Resmî kaydı gösterir misiniz?", "Kısa bilgi verir misiniz?", "Bu seçeneği doğrular mısınız?"],
        "dogrulama": ["CSV kaydını paylaşır mısınız?", "Bu oda hakkında ne biliyorsunuz?", "Resmî sonucu verir misiniz?"],
        "degerlendirme": ["Uygun aracı kullanarak yanıtlar mısınız?", "Araç sonucunu iletir misiniz?", "Doğrulanmış sonucu getirir misiniz?"],
    }[ayrim]
    ornekler = []
    for sira in range(adet):
        tur = sira % 3
        ek = soru_ekleri[(sira // 3) % len(soru_ekleri)]
        if tur == 0:
            oda_tipi = oda_tipleri[(sira // 3) % len(oda_tipleri)]
            argumanlar = {"oda_sorgusu": oda_tipi}
            sonuc = oda_bilgisi(oda_tipi)
            soru = f"{oda_tipi} için oda bilgisi istiyorum. {ek}"
            ad = "oda_bilgisi"
        elif tur == 1:
            oda_tipi = oda_tipleri[(sira // 3) % len(oda_tipleri)]
            gece = ((sira // 3) % 6) + 1
            istek: dict[str, Any] = {
                "oda_tipi": oda_tipi,
                "gece_sayisi": gece,
                "evcil_hayvan": oda_tipi in {"Standart Bahçe Odası", "Bahçe Katı Suit"} and (sira // 3) % 2 == 0,
                "erken_rezervasyon": False,
            }
            argumanlar = {"konaklama_sorgusu": json.dumps(istek, ensure_ascii=False, sort_keys=True)}
            sonuc = konaklama_ucreti(argumanlar["konaklama_sorgusu"])
            soru = f"{oda_tipi} için {gece} gecelik konaklama ücretini hesaplar mısınız? {ek}"
            ad = "konaklama_ucreti"
        else:
            sol = ((sira // 3) % 15) + 2
            sag = ((sira // 5) % 9) + 1
            ifade = f"{sol} * {sag} + {sira % 4}"
            argumanlar = {"ifade": ifade}
            sonuc = hesapla(ifade)
            soru = f"{ifade} işlemini hesaplar mısınız? {ek}"
            ad = "hesapla"
        ornekler.append(_ajan_kaydi(f"{ayrim}-ajan-{sira + 1:03d}", soru, ad, argumanlar, sonuc))
    return ornekler


def _soru_imzasi(ornek: dict[str, Any]) -> str:
    """Benim doğrudan soru tekrarlarını ayırmak için kararlı imza üretir."""
    soru = next(mesaj["content"] for mesaj in ornek["messages"] if mesaj["role"] == "user")
    sade = re.sub(r"\W+", "", soru.casefold())
    return sha256(sade.encode("utf-8")).hexdigest()


def _ornekleri_uret(ayrim: str, sayilar: dict[str, int]) -> list[dict[str, Any]]:
    """Benim üç örnek türünü istenen sayıda birleştirir."""
    return (
        _kimlik_ornekleri(ayrim, sayilar["kimlik"])
        + _rag_ornekleri(ayrim, sayilar["rag"])
        + _ajan_ornekleri(ayrim, sayilar["ajan"])
    )


def _jsonl_yaz(dosya: Path, ornekler: list[dict[str, Any]]) -> None:
    """Benim JSONL eğitim dosyamı UTF-8 olarak yazar."""
    dosya.write_text("\n".join(json.dumps(ornek, ensure_ascii=False, sort_keys=True) for ornek in ornekler) + "\n", encoding="utf-8")


def jsonl_oku(dosya: Path) -> list[dict[str, Any]]:
    """Benim JSONL dosyamı denetim ve ölçüm için okur."""
    return [json.loads(satir) for satir in dosya.read_text(encoding="utf-8").splitlines() if satir.strip()]


def veri_kumelerini_uret() -> dict[str, int]:
    """Benim tekrarlanabilir biçimde 450 eğitim ve ayrı değerlendirme örneklerimi üretir."""
    EGITIM_DIZINI.mkdir(parents=True, exist_ok=True)
    kumeler = {
        EGITIM_DOSYASI: _ornekleri_uret("egitim", {"kimlik": 150, "rag": 150, "ajan": 150}),
        DOGRULAMA_DOSYASI: _ornekleri_uret("dogrulama", {"kimlik": 20, "rag": 20, "ajan": 20}),
        DEGERLENDIRME_DOSYASI: _ornekleri_uret("degerlendirme", {"kimlik": 20, "rag": 20, "ajan": 20}),
    }
    for dosya, ornekler in kumeler.items():
        _jsonl_yaz(dosya, ornekler)
    sablon = {ornek["id"]: {"yanit": "", "arac_cagrisi": ""} for ornek in kumeler[DEGERLENDIRME_DOSYASI]}
    CIKTI_SABLONU_DOSYASI.write_text(json.dumps(sablon, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    rapor = veri_dogrula()
    if rapor["hatalar"]:
        raise ValueError("Veri doğrulaması başarısız: " + "; ".join(rapor["hatalar"]))
    return rapor["sayilar"]


def _arac_cagrisi_gecerli(ornek: dict[str, Any]) -> str | None:
    """Benim ajan kaydındaki JSON, şema ve gerçek araç sonucunu doğrular."""
    if len(ornek.get("arac_cagrilari", [])) != 1:
        return "ajan örneğinde tam bir araç çağrısı olmalıdır"
    cagri = ornek["arac_cagrilari"][0]
    ad = cagri.get("ad")
    argumanlar = cagri.get("argumanlar")
    if ad not in ARAC_SEMALARI or not isinstance(argumanlar, dict):
        return "araç adı veya argüman şeması geçersizdir"
    if set(argumanlar) != set(ARAC_SEMALARI[ad]):
        return "araç argümanları gerçek şemayla uyuşmuyor"
    arac_mesaji = ornek["messages"][2]["content"]
    try:
        arac_jsonu = json.loads(arac_mesaji)
    except json.JSONDecodeError:
        return "araç çağrısı geçerli JSON değildir"
    if arac_jsonu != {"ad": ad, "argumanlar": argumanlar}:
        return "araç JSON'u kayıtla uyuşmuyor"
    if ad == "oda_bilgisi":
        beklenen_sonuc = oda_bilgisi(argumanlar["oda_sorgusu"])
    elif ad == "hesapla":
        beklenen_sonuc = hesapla(argumanlar["ifade"])
    elif ad == "konaklama_ucreti":
        beklenen_sonuc = konaklama_ucreti(argumanlar["konaklama_sorgusu"])
    else:
        return "bu eğitim kümesinde desteklenmeyen araç çağrısı var"
    return None if cagri.get("sonuc") == beklenen_sonuc else "araç sonucu gerçek çağrıyla uyuşmuyor"


def veri_dogrula() -> dict[str, Any]:
    """Benim şema, sayı, kaynak ve ayrım koşullarımı ayrıntılı olarak denetler."""
    dosyalar = {"egitim": EGITIM_DOSYASI, "dogrulama": DOGRULAMA_DOSYASI, "degerlendirme": DEGERLENDIRME_DOSYASI}
    hatalar: list[str] = []
    kumeler: dict[str, list[dict[str, Any]]] = {}
    for ad, dosya in dosyalar.items():
        if not dosya.exists():
            hatalar.append(f"{ad} dosyası yok")
            continue
        try:
            kumeler[ad] = jsonl_oku(dosya)
        except json.JSONDecodeError:
            hatalar.append(f"{ad} JSONL satırlarından biri geçersiz")
    if set(kumeler) != set(dosyalar):
        return {"hatalar": hatalar, "sayilar": {}}

    tum_idler: set[str] = set()
    soru_imzalari: dict[str, set[str]] = {}
    rag_kaynaklari: dict[str, set[str]] = {}
    for ayrim, ornekler in kumeler.items():
        tur_sayilari = Counter(ornek.get("tur") for ornek in ornekler)
        if tur_sayilari.keys() != {"kimlik", "rag", "ajan"}:
            hatalar.append(f"{ayrim} üç örnek türünü içermiyor")
        if ayrim == "egitim" and len(ornekler) < 400:
            hatalar.append("eğitim kümesinde en az 400 örnek yok")
        soru_imzalari[ayrim] = set()
        rag_kaynaklari[ayrim] = set()
        for ornek in ornekler:
            gerekli = {"id", "tur", "kaynak", "beklenti", "messages"}
            if not gerekli <= set(ornek):
                hatalar.append(f"{ornek.get('id', 'bilinmeyen')} temel şemayı karşılamıyor")
                continue
            if ornek["id"] in tum_idler:
                hatalar.append(f"yinelenen id: {ornek['id']}")
            tum_idler.add(ornek["id"])
            mesajlar = ornek["messages"]
            if not isinstance(mesajlar, list) or any(set(mesaj) != {"role", "content"} for mesaj in mesajlar):
                hatalar.append(f"{ornek['id']} mesaj şeması geçersiz")
                continue
            if mesajlar[0] != _mesaj("system", KIMLIK_METNI):
                hatalar.append(f"{ornek['id']} kimlik metnini değiştirmiş")
            soru_imzalari[ayrim].add(_soru_imzasi(ornek))
            if ornek["tur"] == "rag":
                kaynak = ornek["kaynak"]
                kaynak_id = kaynak.get("id")
                beklenen_kaynak = _REHBER_KAYNAK_DIZINI.get(kaynak_id)
                if kaynak.get("tur") != "rehber.pdf" or not ornek.get("baglam") or beklenen_kaynak is None:
                    hatalar.append(f"{ornek['id']} RAG kaynağı eksik")
                elif kaynak.get("bolum") != beklenen_kaynak[1] or ornek["baglam"] != beklenen_kaynak[2]:
                    hatalar.append(f"{ornek['id']} RAG kaynağı rehber kaydıyla uyuşmuyor")
                else:
                    rag_kaynaklari[ayrim].add(kaynak_id)
                cevap = mesajlar[-1]["content"].casefold()
                if not all(ifade.casefold() in cevap for ifade in ornek["beklenti"]["rag_zorunlu_ifadeler"]):
                    hatalar.append(f"{ornek['id']} RAG cevabı kaynağıyla uyuşmuyor")
            if ornek["tur"] == "ajan":
                hata = _arac_cagrisi_gecerli(ornek)
                if hata:
                    hatalar.append(f"{ornek['id']}: {hata}")
    for ilk, ikinci in (("egitim", "dogrulama"), ("egitim", "degerlendirme"), ("dogrulama", "degerlendirme")):
        if soru_imzalari[ilk] & soru_imzalari[ikinci]:
            hatalar.append(f"{ilk} ve {ikinci} arasında doğrudan soru sızıntısı var")
        if rag_kaynaklari[ilk] & rag_kaynaklari[ikinci]:
            hatalar.append(f"{ilk} ve {ikinci} arasında RAG kaynak sızıntısı var")
    sayilar = {ad: len(ornekler) for ad, ornekler in kumeler.items()}
    sayilar["toplam"] = sum(sayilar.values())
    return {"hatalar": hatalar, "sayilar": sayilar, "tur_sayilari": {ad: dict(Counter(ornek["tur"] for ornek in ornekler)) for ad, ornekler in kumeler.items()}}


def degerlendirme_metriklerini_hesapla(model_ciktilari: dict[str, dict[str, str]]) -> dict[str, Any]:
    """Benim eğitim öncesi ve sonrası aynı değerlendirme kümesinde metrikleri hesaplar."""
    ornekler = jsonl_oku(DEGERLENDIRME_DOSYASI)
    sayac = Counter()
    paydalar = Counter()
    for ornek in ornekler:
        cikti = model_ciktilari.get(ornek["id"], {})
        yanit = cikti.get("yanit", "")
        paydalar["cevap_isareti_dogrulugu"] += 1
        if not CEVAP_SONU_ISARETI or yanit.endswith(CEVAP_SONU_ISARETI):
            sayac["cevap_isareti_dogrulugu"] += 1
        if ornek["tur"] == "kimlik":
            paydalar["kimlik_dogrulugu"] += 1
            if all(ifade.casefold() in yanit.casefold() for ifade in ornek["beklenti"]["kimlik_dogrulama"]):
                sayac["kimlik_dogrulugu"] += 1
        elif ornek["tur"] == "rag":
            paydalar["rag_dogrulugu"] += 1
            if all(ifade.casefold() in yanit.casefold() for ifade in ornek["beklenti"]["rag_zorunlu_ifadeler"]):
                sayac["rag_dogrulugu"] += 1
        elif ornek["tur"] == "ajan":
            paydalar["gecerli_json"] += 1
            paydalar["dogru_arac"] += 1
            try:
                cagri = json.loads(cikti.get("arac_cagrisi", ""))
                json_gecerli = isinstance(cagri, dict)
            except json.JSONDecodeError:
                cagri = {}
                json_gecerli = False
            if json_gecerli:
                sayac["gecerli_json"] += 1
            if cagri == {"ad": ornek["beklenti"]["dogru_arac"], "argumanlar": ornek["beklenti"]["argumanlar"]}:
                sayac["dogru_arac"] += 1
    metrikler = {ad: (sayac[ad] / payda if payda else None) for ad, payda in paydalar.items()}
    return {"ornek_sayisi": len(ornekler), "metrikler": metrikler, "dogru_sayilari": dict(sayac), "paydalar": dict(paydalar)}


if __name__ == "__main__":
    print(json.dumps(veri_kumelerini_uret(), ensure_ascii=False, indent=2))
