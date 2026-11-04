"""Benim hoca defteriyle uyumlu eğitim veri doğrulama testlerim."""

from begonia_egitim_dogrulama import ARAC_PARAMETRELERI, kumeleri_dogrula, ornegi_dogrula


def _ajan_ornegi(soru: str = "Aile Odası için bilgi verir misiniz?") -> dict[str, object]:
    return {
        "tur": "ajan",
        "messages": [
            {"role": "system", "content": "Sistem"},
            {"role": "user", "content": soru},
            {"role": "assistant", "content": '{"dusunce":"Oda bilgisini araçla öğrenmeliyim.","arac":"oda_bilgisi","argumanlar":{"oda_sorgusu":"Aile Odası"}}'},
        ],
    }


def test_gercek_arac_parametreleri_koddan_okunur() -> None:
    assert ARAC_PARAMETRELERI == {
        "rehberde_ara": ("sorgu",),
        "oda_bilgisi": ("oda_sorgusu",),
        "hesapla": ("ifade",),
        "konaklama_ucreti": ("konaklama_sorgusu",),
    }


def test_ajan_ve_iki_turlu_ajan_semasi_gecerlidir() -> None:
    ajan = _ajan_ornegi()
    ajan2 = {
        "tur": "ajan2",
        "messages": ajan["messages"][:3]
        + [
            {"role": "user", "content": "Araç sonucu: Aile Odası: 4 kişilik."},
            {"role": "assistant", "content": '{"dusunce":"Araç sonucu geldi.","cevap":"Aile Odası 4 kişiliktir."}'},
        ],
    }

    assert ornegi_dogrula(ajan) == []
    assert ornegi_dogrula(ajan2) == []


def test_uydurulmus_arac_ve_sizinti_reddedilir() -> None:
    hatali = _ajan_ornegi()
    hatali["messages"][2]["content"] = '{"dusunce":"","arac":"oda_ayirt","argumanlar":{"oda":"Aile"}}'
    egitim = [_ajan_ornegi(f"Eğitim sorusu {sira}") for sira in range(400)]
    egitim.extend([
        {"tur": "kimlik", "messages": [{"role": "user", "content": "Kimlik"}, {"role": "assistant", "content": "Begonia AI"}]},
        {"tur": "rag", "messages": [{"role": "system", "content": "Bağlam"}, {"role": "user", "content": "RAG"}, {"role": "assistant", "content": "Yanıt"}]},
        {"tur": "ajan2", "messages": [
            {"role": "system", "content": "Sistem"}, {"role": "user", "content": "İki tur"},
            {"role": "assistant", "content": '{"dusunce":"","arac":"hesapla","argumanlar":{"ifade":"2+2"}}'},
            {"role": "user", "content": "Araç sonucu: 4"},
            {"role": "assistant", "content": '{"dusunce":"","cevap":"4"}'},
        ]},
    ])

    assert any("uydurulmuş araç" in hata for hata in ornegi_dogrula(hatali))
    assert any("sızıntısı" in hata for hata in kumeleri_dogrula(egitim, [_ajan_ornegi("Eğitim sorusu 1")]))
