"""Begonia AI ajanım için resmî veriye dayalı araçlar."""

import ast
import csv
import json
import operator
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Callable

from proje import ODA_TABLOSU_SUTUNLARI, ODALAR_DOSYASI


def rehberde_ara(sorgu: str) -> str:
    """Rehber araması için veri hazır olana kadarki güvenli yanıtı döndürür."""
    if not sorgu.strip():
        return "Lütfen rehberde aramamı istediğiniz konuyu yazın."
    return "Resmî rehber.pdf henüz eklenmediği için rehberde doğrulanmış bilgi sunamıyorum."


def oda_bilgisi(oda_sorgusu: str) -> str:
    """Benim oda türüne tam eşleşmeyle resmî oda bilgisini döndürür."""
    if not isinstance(oda_sorgusu, str) or not oda_sorgusu.strip():
        return "Lütfen bilgi istediğiniz oda türünü tam adıyla yazın."

    oda = _oda_bul(oda_sorgusu.strip())
    if oda is None:
        return _oda_bulunamadi_mesaji()

    return (
        f"{oda['oda_tipi']}: {oda['kapasite']} kişilik, {oda['metrekare']} m², "
        f"{oda['manzara']} manzaralı, gecelik {_tl(oda['gecelik_fiyat_tl'])} TL, "
        f"evcil hayvan {'kabul edilir' if oda['evcil_hayvan'] == 'evet' else 'kabul edilmez'}, "
        f"toplam {oda['oda_sayisi']} oda."
    )


_ISLEMLER: dict[type[ast.operator], Callable[[float, float], float]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}


def hesapla(ifade: str) -> str:
    """Dört işlem içeren güvenli bir sayısal ifadeyi hesaplar."""
    try:
        sonuc = _hesapla_dugumu(ast.parse(ifade, mode="eval").body)
    except (SyntaxError, TypeError, ValueError, ZeroDivisionError):
        return "Yalnızca sayılar ve +, -, * , / işlemleriyle bir hesaplama yazın."
    return str(sonuc)


def _hesapla_dugumu(dugum: ast.AST) -> float:
    """Yalnızca izin verilen sayı ve dört işlem düğümlerini değerlendirir."""
    if isinstance(dugum, ast.Constant) and isinstance(dugum.value, (int, float)):
        return dugum.value
    if isinstance(dugum, ast.UnaryOp) and isinstance(dugum.op, (ast.UAdd, ast.USub)):
        deger = _hesapla_dugumu(dugum.operand)
        return deger if isinstance(dugum.op, ast.UAdd) else -deger
    if isinstance(dugum, ast.BinOp) and type(dugum.op) in _ISLEMLER:
        sol = _hesapla_dugumu(dugum.left)
        sag = _hesapla_dugumu(dugum.right)
        return _ISLEMLER[type(dugum.op)](sol, sag)
    raise ValueError("İzin verilmeyen ifade")


def konaklama_ucreti(konaklama_sorgusu: str) -> str:
    """Benim JSON metninden resmî konaklama ücretini her durumda metin olarak döndürür."""
    if not isinstance(konaklama_sorgusu, str) or not konaklama_sorgusu.strip():
        return _ucret_girdi_mesaji()

    try:
        istek = json.loads(konaklama_sorgusu)
    except json.JSONDecodeError:
        return _ucret_girdi_mesaji()

    if not isinstance(istek, dict):
        return "Konaklama bilgisi JSON nesnesi olmalıdır."

    izinli_alanlar = {
        "oda_tipi",
        "gece_sayisi",
        "evcil_hayvan",
        "erken_rezervasyon",
        "rezervasyon_tarihi",
        "giris_tarihi",
    }
    bilinmeyen_alanlar = set(istek) - izinli_alanlar
    if bilinmeyen_alanlar:
        return "Bilinmeyen alanlar var: " + ", ".join(sorted(bilinmeyen_alanlar)) + "."

    oda_tipi = istek.get("oda_tipi")
    if not isinstance(oda_tipi, str) or not oda_tipi.strip():
        return "'oda_tipi' alanını odalar.csv içindeki tam oda adıyla yazın."
    oda = _oda_bul(oda_tipi.strip())
    if oda is None:
        return _oda_bulunamadi_mesaji()

    gece_sayisi = istek.get("gece_sayisi")
    if isinstance(gece_sayisi, bool) or not isinstance(gece_sayisi, int) or gece_sayisi < 1:
        return "'gece_sayisi' alanı 1 veya daha büyük tam sayı olmalıdır."

    evcil_hayvan = istek.get("evcil_hayvan", False)
    if not isinstance(evcil_hayvan, bool):
        return "'evcil_hayvan' alanı true veya false olmalıdır."
    if evcil_hayvan and oda["evcil_hayvan"] != "evet":
        return (
            f"{oda['oda_tipi']} evcil hayvan için uygun değildir. Rehbere göre evcil hayvanlı "
            "misafirler yalnızca bahçe katındaki, evcil hayvan kabul eden odalarda kalabilir."
        )

    erken_rezervasyon = istek.get("erken_rezervasyon", False)
    if not isinstance(erken_rezervasyon, bool):
        return "'erken_rezervasyon' alanı true veya false olmalıdır."

    tarih_sonucu = _erken_rezervasyon_durumu(istek, erken_rezervasyon)
    if isinstance(tarih_sonucu, str):
        return tarih_sonucu
    gun_farki, indirim_uygulanir = tarih_sonucu

    oda_bedeli = int(oda["gecelik_fiyat_tl"]) * gece_sayisi
    evcil_hayvan_bedeli = 600 * gece_sayisi if evcil_hayvan else 0
    indirim = oda_bedeli * 15 // 100 if indirim_uygulanir else 0
    toplam = oda_bedeli - indirim + evcil_hayvan_bedeli

    kalemler = [
        f"Oda bedeli: {_tl(oda_bedeli)} TL ({gece_sayisi} gece x {_tl(oda['gecelik_fiyat_tl'])} TL)."
    ]
    if evcil_hayvan:
        kalemler.append(f"Evcil hayvan temizlik ücreti: {_tl(evcil_hayvan_bedeli)} TL (gecelik 600 TL).")
    if erken_rezervasyon:
        if indirim_uygulanir:
            kalemler.append(
                f"Erken rezervasyon indirimi: -{_tl(indirim)} TL (rezervasyon ile giriş arasında {gun_farki} gün, %15)."
            )
        elif gun_farki is None:
            kalemler.append("Erken rezervasyon indirimi uygulanmadı; iki tarih de verilmedi.")
        else:
            kalemler.append(
                f"Erken rezervasyon indirimi uygulanmadı; rezervasyon ile giriş arasında {gun_farki} gün var, en az 60 gün gerekir."
            )
    elif gun_farki is not None:
        kalemler.append(f"Rezervasyon ile giriş arasındaki süre {gun_farki} gün; erken_rezervasyon false olduğu için indirim uygulanmadı.")
    kalemler.append(f"Toplam konaklama ücreti: {_tl(toplam)} TL.")
    return " ".join(kalemler)


@lru_cache(maxsize=1)
def _odalari_oku() -> tuple[dict[str, str], ...]:
    """Benim oda tablosunu doğrulayıp tekrar kullanılabilir biçimde okur."""
    try:
        with Path(ODALAR_DOSYASI).open(encoding="utf-8-sig", newline="") as dosya:
            okuyucu = csv.DictReader(dosya)
            if tuple(okuyucu.fieldnames or ()) != ODA_TABLOSU_SUTUNLARI:
                return ()
            odalar = tuple(okuyucu)
    except (OSError, csv.Error):
        return ()

    gerekli_degerler = set(ODA_TABLOSU_SUTUNLARI)
    if not odalar or any(set(oda) != gerekli_degerler for oda in odalar):
        return ()
    try:
        for oda in odalar:
            if oda["evcil_hayvan"] not in {"evet", "hayır"}:
                return ()
            if any(int(oda[alan]) < 1 for alan in ("kapasite", "metrekare", "gecelik_fiyat_tl", "oda_sayisi")):
                return ()
    except (TypeError, ValueError):
        return ()
    return odalar


def _oda_bul(oda_tipi: str) -> dict[str, str] | None:
    """Benim yalnızca oda türü tam eşleştiğinde ilgili satırı bulur."""
    return next((oda for oda in _odalari_oku() if oda["oda_tipi"] == oda_tipi), None)


def _oda_bulunamadi_mesaji() -> str:
    """Benim geçerli oda türlerini içeren anlaşılır hatayı üretir."""
    odalar = _odalari_oku()
    if not odalar:
        return "Oda tablosu okunamadı veya beklenen sütunları içermiyor."
    oda_tipleri = ", ".join(oda["oda_tipi"] for oda in odalar)
    return f"Oda türü bulunamadı. Lütfen şu oda türlerinden birini tam olarak yazın: {oda_tipleri}."


def _erken_rezervasyon_durumu(istek: dict[str, object], erken_rezervasyon: bool) -> tuple[int | None, bool] | str:
    """Benim iki tarih varsa gün farkını hesaplar ve %15 indirimi doğrular."""
    rezervasyon = istek.get("rezervasyon_tarihi")
    giris = istek.get("giris_tarihi")
    if rezervasyon is None and giris is None:
        return None, False
    if not isinstance(rezervasyon, str) or not isinstance(giris, str):
        return "Erken rezervasyon kontrolü için 'rezervasyon_tarihi' ve 'giris_tarihi' birlikte YYYY-AA-GG biçiminde verilmelidir."
    try:
        rezervasyon_tarihi = date.fromisoformat(rezervasyon)
        giris_tarihi = date.fromisoformat(giris)
    except ValueError:
        return "Tarihler YYYY-AA-GG biçiminde geçerli takvim tarihleri olmalıdır."
    gun_farki = (giris_tarihi - rezervasyon_tarihi).days
    if gun_farki < 0:
        return "Giriş tarihi rezervasyon tarihinden önce olamaz."
    return gun_farki, erken_rezervasyon and gun_farki >= 60


def _tl(tutar: int | str) -> str:
    """Benim TL tutarlarını Türkçe binlik ayırıcıyla yazar."""
    return f"{int(tutar):,}".replace(",", ".")


def _ucret_girdi_mesaji() -> str:
    """Benim ücret aracı için beklenen JSON biçimini açıklar."""
    return (
        "Konaklama bilgisini JSON olarak yazın: "
        '{"oda_tipi": "Standart Bahçe Odası", "gece_sayisi": 2, '
        '"evcil_hayvan": false, "erken_rezervasyon": false}. '
        "Erken rezervasyon için isteğe bağlı 'rezervasyon_tarihi' ve 'giris_tarihi' alanlarını YYYY-AA-GG biçiminde ekleyin."
    )
