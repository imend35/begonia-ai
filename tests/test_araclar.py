"""Benim resmî oda verisi ve ücret araçlarım için birim testlerim."""

import csv
import json
from pathlib import Path

from araclar import hesapla, konaklama_ucreti, oda_bilgisi, rehberde_ara
from proje import CEVAP_SONU_ISARETI, KIMLIK_METNI, ODALAR_DOSYASI, ODA_TABLOSU_SUTUNLARI, TEST_SORULARI_DOSYASI


def _ucret_istegi(**ek_alanlar: object) -> str:
    """Benim ücret aracı çağrılarım için geçerli varsayılan JSON'u kurar."""
    istek: dict[str, object] = {
        "oda_tipi": "Standart Bahçe Odası",
        "gece_sayisi": 2,
        "evcil_hayvan": False,
        "erken_rezervasyon": False,
    }
    istek.update(ek_alanlar)
    return json.dumps(istek, ensure_ascii=False)


def test_hesapla_dort_islem_yapar() -> None:
    assert hesapla("2 + 3 * 4") == "14"


def test_hesapla_gecersiz_ifadeyi_reddeder() -> None:
    assert "Yalnızca sayılar" in hesapla("__import__('os')")


def test_rehber_arama_veri_olmadan_bilgi_uydurmaz() -> None:
    assert "henüz eklenmediği" in rehberde_ara("kahvaltı")


def test_oda_bilgisi_tam_eslesen_oda_verisini_dondurur() -> None:
    sonuc = oda_bilgisi("Aile Odası")

    assert "4 kişilik" in sonuc
    assert "40 m²" in sonuc
    assert "7.400 TL" in sonuc
    assert "evcil hayvan kabul edilmez" in sonuc


def test_oda_bilgisi_kismi_ve_hatali_eslesmeyi_reddeder() -> None:
    assert "tam olarak" in oda_bilgisi("Aile")
    assert "tam adıyla" in oda_bilgisi("")


def test_konaklama_ucreti_csv_fiyatindan_hesaplanir() -> None:
    sonuc = konaklama_ucreti(_ucret_istegi(oda_tipi="Deniz Manzaralı Suit", gece_sayisi=3))

    assert "Oda bedeli: 34.500 TL" in sonuc
    assert "Toplam konaklama ücreti: 34.500 TL" in sonuc


def test_evcil_hayvan_uygun_odada_gecelik_ucret_ekler() -> None:
    sonuc = konaklama_ucreti(_ucret_istegi(evcil_hayvan=True))

    assert "Evcil hayvan temizlik ücreti: 1.200 TL" in sonuc
    assert "Toplam konaklama ücreti: 9.600 TL" in sonuc


def test_evcil_hayvan_uygun_olmayan_odada_reddedilir() -> None:
    sonuc = konaklama_ucreti(_ucret_istegi(oda_tipi="Standart Deniz Odası", evcil_hayvan=True))

    assert "evcil hayvan için uygun değildir" in sonuc
    assert "bahçe katındaki" in sonuc


def test_konaklama_ucreti_hatali_girdilerde_metne_doner() -> None:
    assert "JSON" in konaklama_ucreti("iki gece")
    assert "1 veya daha büyük" in konaklama_ucreti(_ucret_istegi(gece_sayisi=0))
    assert "true veya false" in konaklama_ucreti(_ucret_istegi(evcil_hayvan="evet"))
    assert "Oda türü bulunamadı" in konaklama_ucreti(_ucret_istegi(oda_tipi="Suit"))
    assert "Bilinmeyen alanlar" in konaklama_ucreti(_ucret_istegi(kisi_sayisi=2))


def test_erken_rezervasyon_tarih_olmadan_otomatik_uygulanmaz() -> None:
    sonuc = konaklama_ucreti(_ucret_istegi(erken_rezervasyon=True))

    assert "iki tarih de verilmedi" in sonuc
    assert "Toplam konaklama ücreti: 8.400 TL" in sonuc


def test_erken_rezervasyon_60_gunde_yuzde_15_uygular() -> None:
    sonuc = konaklama_ucreti(
        _ucret_istegi(
            gece_sayisi=1,
            erken_rezervasyon=True,
            rezervasyon_tarihi="2027-01-01",
            giris_tarihi="2027-03-02",
        )
    )

    assert "60 gün, %15" in sonuc
    assert "-630 TL" in sonuc
    assert "Toplam konaklama ücreti: 3.570 TL" in sonuc


def test_erken_rezervasyon_60_gunden_azsa_uygulanmaz() -> None:
    sonuc = konaklama_ucreti(
        _ucret_istegi(
            erken_rezervasyon=True,
            rezervasyon_tarihi="2027-01-01",
            giris_tarihi="2027-03-01",
        )
    )

    assert "59 gün var" in sonuc
    assert "Toplam konaklama ücreti: 8.400 TL" in sonuc


def test_tarih_dogrulamasi_ve_indirim_istegi_kontrol_edilir() -> None:
    assert "birlikte" in konaklama_ucreti(
        _ucret_istegi(erken_rezervasyon=True, rezervasyon_tarihi="2027-01-01")
    )
    assert "geçerli takvim tarihleri" in konaklama_ucreti(
        _ucret_istegi(erken_rezervasyon=True, rezervasyon_tarihi="2027-02-30", giris_tarihi="2027-05-01")
    )
    assert "önce olamaz" in konaklama_ucreti(
        _ucret_istegi(erken_rezervasyon=True, rezervasyon_tarihi="2027-05-01", giris_tarihi="2027-04-01")
    )
    sonuc = konaklama_ucreti(
        _ucret_istegi(rezervasyon_tarihi="2027-01-01", giris_tarihi="2027-04-01")
    )
    assert "90 gün" in sonuc
    assert "erken_rezervasyon false" in sonuc


def test_veri_butunlugu_oda_ve_soru_tablolarinda_korunur() -> None:
    with Path(ODALAR_DOSYASI).open(encoding="utf-8-sig", newline="") as dosya:
        odalar = list(csv.DictReader(dosya))
        assert tuple(odalar[0]) == ODA_TABLOSU_SUTUNLARI
    assert len(odalar) == 8
    assert {oda["evcil_hayvan"] for oda in odalar} == {"evet", "hayır"}
    assert all(int(oda["gecelik_fiyat_tl"]) > 0 for oda in odalar)

    with Path(TEST_SORULARI_DOSYASI).open(encoding="utf-8-sig", newline="") as dosya:
        sorular = list(csv.DictReader(dosya))
    assert len(sorular) == 15
    assert sorular[:13][-1]["soru"] == "Düğün organizasyonu yapıyor musunuz?"
    assert [soru["kaynak"] for soru in sorular[-2:]] == [
        "araç: konaklama_ucreti",
        "araç: konaklama_ucreti",
    ]


def test_kimlik_metni_ve_cevap_sonu_isareti_degismez() -> None:
    assert KIMLIK_METNI == """Sen Begonvil Otel için çalışan Begonia AI adlı Türkçe otel resepsiyon asistanısın.
Görevin konuklara yalnızca resmî otel rehberinde ve sağlanan verilerde bulunan bilgilerle yardımcı olmaktır.
Rehberde veya sağlanan verilerde bulunmayan oda, fiyat, kampanya, kural, hizmet ya da rezervasyon bilgisini uydurma.
Bilgi bulunmadığında bunu açıkça belirt ve resmî resepsiyonla iletişime geçilmesini öner.
Yanıtlarını Türkçe, nazik ve kısa tut."""
    assert CEVAP_SONU_ISARETI == ""
