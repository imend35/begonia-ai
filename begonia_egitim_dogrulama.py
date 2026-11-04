"""Benim hoca defteriyle uyumlu Begonia eğitim verisi denetimlerim."""

import inspect
import json
import re
from hashlib import sha256
from typing import Any

import araclar


ARAC_PARAMETRELERI = {
    ad: tuple(inspect.signature(getattr(araclar, ad)).parameters)
    for ad in ("rehberde_ara", "oda_bilgisi", "hesapla", "konaklama_ucreti")
}
GECERLI_TURLER = {"kimlik", "rag", "ajan", "ajan2"}


def soru_imzasi(ornek: dict[str, Any]) -> str:
    """Benim aynı kullanıcı sorusunu ayrımlar arasında bulmamı sağlar."""
    soru = next(mesaj["content"] for mesaj in ornek["messages"] if mesaj["role"] == "user")
    sade = re.sub(r"\W+", "", soru.casefold())
    return sha256(sade.encode("utf-8")).hexdigest()


def _arac_jsonu_gecerli(metin: str) -> tuple[bool, str]:
    """Benim ajan kararındaki araç adı ve argüman şemasını denetler."""
    try:
        karar = json.loads(metin)
    except json.JSONDecodeError:
        return False, "ajan kararı geçerli JSON değil"
    if not isinstance(karar, dict) or not {"dusunce", "arac", "argumanlar"} <= set(karar):
        return False, "ajan kararında dusunce, arac ve argumanlar bulunmalı"
    arac = karar["arac"]
    if arac not in ARAC_PARAMETRELERI:
        return False, f"uydurulmuş araç: {arac}"
    if not isinstance(karar["argumanlar"], dict) or tuple(karar["argumanlar"]) != ARAC_PARAMETRELERI[arac]:
        return False, f"{arac} için argüman şeması yanlış"
    return True, ""


def ornegi_dogrula(ornek: dict[str, Any]) -> list[str]:
    """Benim tek eğitim örneğinin tur/messages ve araç biçimini denetler."""
    hatalar: list[str] = []
    if set(ornek) != {"tur", "messages"}:
        return ["örnek yalnızca tur ve messages alanlarını içermeli"]
    tur = ornek["tur"]
    mesajlar = ornek["messages"]
    if tur not in GECERLI_TURLER:
        hatalar.append("geçersiz tur")
    if not isinstance(mesajlar, list) or not mesajlar:
        return hatalar + ["messages boş olmayan liste olmalı"]
    if any(set(mesaj) != {"role", "content"} or not isinstance(mesaj["content"], str) for mesaj in mesajlar):
        return hatalar + ["messages şeması geçersiz"]
    if tur in {"kimlik", "rag"} and [mesaj["role"] for mesaj in mesajlar][-2:] != ["user", "assistant"]:
        hatalar.append("kimlik/RAG örneği user-assistant ile bitmeli")
    if tur == "rag" and mesajlar[0]["role"] != "system":
        hatalar.append("RAG örneği bağlam içeren system mesajıyla başlamalı")
    if tur == "ajan":
        if len(mesajlar) != 3 or [mesaj["role"] for mesaj in mesajlar] != ["system", "user", "assistant"]:
            hatalar.append("ajan örneği üç turlu system-user-assistant olmalı")
        else:
            gecerli, hata = _arac_jsonu_gecerli(mesajlar[2]["content"])
            if not gecerli:
                hatalar.append(hata)
    if tur == "ajan2":
        roller = [mesaj["role"] for mesaj in mesajlar]
        if len(mesajlar) != 5 or roller != ["system", "user", "assistant", "user", "assistant"]:
            hatalar.append("ajan2 örneği beş turlu sistem-akışı olmalı")
        else:
            gecerli, hata = _arac_jsonu_gecerli(mesajlar[2]["content"])
            if not gecerli:
                hatalar.append(hata)
            if not mesajlar[3]["content"].startswith("Araç sonucu: "):
                hatalar.append("ajan2 araç sonucu kullanıcı turunda açıkça yazılmalı")
            try:
                son_karar = json.loads(mesajlar[4]["content"])
                if not isinstance(son_karar, dict) or set(son_karar) != {"dusunce", "cevap"}:
                    hatalar.append("ajan2 son kararı dusunce ve cevap içermeli")
            except json.JSONDecodeError:
                hatalar.append("ajan2 son kararı geçerli JSON değil")
    return hatalar


def kumeleri_dogrula(egitim: list[dict[str, Any]], test: list[dict[str, Any]]) -> list[str]:
    """Benim örnek sayısı, şema ve eğitim-test ayrımını birlikte denetler."""
    hatalar = [hata for ornek in egitim + test for hata in ornegi_dogrula(ornek)]
    if len(egitim) < 400:
        hatalar.append("eğitim kümesinde en az 400 geçerli örnek yok")
    if not {ornek["tur"] for ornek in egitim} >= GECERLI_TURLER:
        hatalar.append("eğitim kümesinde dört örnek türü de yok")
    if {soru_imzasi(ornek) for ornek in egitim} & {soru_imzasi(ornek) for ornek in test}:
        hatalar.append("eğitim ve test kümeleri arasında doğrudan soru sızıntısı var")
    return hatalar
