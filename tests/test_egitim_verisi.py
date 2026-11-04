"""Benim ADIM 3A eğitim verisi ve ölçüm altyapısı testlerim."""

import json

from egitim_verisi import (
    CIKTI_SABLONU_DOSYASI,
    DEGERLENDIRME_DOSYASI,
    DOGRULAMA_DOSYASI,
    EGITIM_DOSYASI,
    degerlendirme_metriklerini_hesapla,
    jsonl_oku,
    veri_dogrula,
)


def test_egitim_verisi_semasi_sayisi_kaynagi_ve_ayrimi_gecerlidir() -> None:
    rapor = veri_dogrula()

    assert rapor["hatalar"] == []
    assert rapor["sayilar"] == {"egitim": 450, "dogrulama": 60, "degerlendirme": 60, "toplam": 570}
    assert rapor["tur_sayilari"]["egitim"] == {"kimlik": 150, "rag": 150, "ajan": 150}


def test_egitim_dogrulama_ve_degerlendirme_sorulari_birbirinden_ayridir() -> None:
    kumeler = [jsonl_oku(dosya) for dosya in (EGITIM_DOSYASI, DOGRULAMA_DOSYASI, DEGERLENDIRME_DOSYASI)]
    sorular = [{ornek["messages"][1]["content"].casefold() for ornek in kume} for kume in kumeler]

    assert not sorular[0] & sorular[1]
    assert not sorular[0] & sorular[2]
    assert not sorular[1] & sorular[2]

    rag_kaynaklari = [
        {ornek["kaynak"]["id"] for ornek in kume if ornek["tur"] == "rag"}
        for kume in kumeler
    ]
    assert not rag_kaynaklari[0] & rag_kaynaklari[1]
    assert not rag_kaynaklari[0] & rag_kaynaklari[2]
    assert not rag_kaynaklari[1] & rag_kaynaklari[2]


def test_ajan_cagrilari_gecerli_json_ve_gercek_arac_sonucudur() -> None:
    for dosya in (EGITIM_DOSYASI, DOGRULAMA_DOSYASI, DEGERLENDIRME_DOSYASI):
        for ornek in jsonl_oku(dosya):
            if ornek["tur"] != "ajan":
                continue
            arac_jsonu = json.loads(ornek["messages"][2]["content"])
            assert arac_jsonu["ad"] == ornek["arac_cagrilari"][0]["ad"]
            assert arac_jsonu["argumanlar"] == ornek["arac_cagrilari"][0]["argumanlar"]
            assert ornek["messages"][-1]["content"] == ornek["arac_cagrilari"][0]["sonuc"]


def test_olcum_altyapisi_altin_ciktilarla_tum_metrikleri_hesaplar() -> None:
    ciktilar = {}
    for ornek in jsonl_oku(DEGERLENDIRME_DOSYASI):
        cikti = {"yanit": ornek["messages"][-1]["content"], "arac_cagrisi": ""}
        if ornek["tur"] == "ajan":
            cikti["arac_cagrisi"] = ornek["messages"][2]["content"]
        ciktilar[ornek["id"]] = cikti

    rapor = degerlendirme_metriklerini_hesapla(ciktilar)

    assert rapor["ornek_sayisi"] == 60
    assert rapor["metrikler"] == {
        "cevap_isareti_dogrulugu": 1.0,
        "kimlik_dogrulugu": 1.0,
        "rag_dogrulugu": 1.0,
        "gecerli_json": 1.0,
        "dogru_arac": 1.0,
    }


def test_degerlendirme_cikti_sablonu_ayni_sorular_icin_hazirdir() -> None:
    sablon = json.loads(CIKTI_SABLONU_DOSYASI.read_text(encoding="utf-8"))

    assert set(sablon) == {ornek["id"] for ornek in jsonl_oku(DEGERLENDIRME_DOSYASI)}
    assert all(cikti == {"yanit": "", "arac_cagrisi": ""} for cikti in sablon.values())
