"""Begonia ADIM 3B Colab defterinin çevrimdışı yapısal testleri."""

import ast
import json
from pathlib import Path


DEFTER = Path(__file__).resolve().parents[1] / "notebooks" / "Begonia_AI_Egitim.ipynb"


def _defteri_oku() -> dict[str, object]:
    return json.loads(DEFTER.read_text(encoding="utf-8"))


def _kaynak() -> str:
    return "\n".join(hucre["source"] for hucre in _defteri_oku()["cells"])


def test_defter_gecerli_ve_hoca_referansini_koruyor() -> None:
    defter = _defteri_oku()

    assert defter["nbformat"] == 4
    assert len(defter["cells"]) >= 20
    assert {hucre["cell_type"] for hucre in defter["cells"]} == {"code", "markdown"}
    assert "Oturum_son_hafta(2).ipynb" in _kaynak()
    assert "adim_3a_egitim_hazirligi.ipynb" in _kaynak()


def test_gercek_veriyi_hoca_tur_messages_semasina_donusturur() -> None:
    kaynak = _kaynak()

    for dosya in ("'rehber': KOK / 'data' / 'rehber.pdf'", "'odalar': KOK / 'data' / 'odalar.csv'", "'test_sorulari': KOK / 'data' / 'test_sorulari.csv'"):
        assert dosya in kaynak
    assert "assert len(HOCA_KUMELERI['egitim']) == 450" in kaynak
    for tur in ("'kimlik'", "'rag'", "'ajan'", "'ajan2'"):
        assert tur in kaynak
    assert "Araç sonucu: " in kaynak
    assert "ARAC_PARAMETRELERI" in kaynak
    assert "for ilk, ikinci in [('egitim', 'dogrulama'), ('egitim', 'degerlendirme'), ('dogrulama', 'degerlendirme')]" in kaynak


def test_qlora_plani_egitim_ve_tekrarlanabilir_degerlendirme_vardir() -> None:
    kaynak = _kaynak()

    assert "bnb_4bit_quant_type='nf4'" in kaynak
    assert "'r': 16, 'lora_alpha': 32, 'lora_dropout': 0.05" in kaynak
    assert "'num_train_epochs': 3" in kaynak
    assert "degerlendir_model" in kaynak
    assert "ajan_json" in kaynak
    assert "ajan_arac" in kaynak
    assert "ONCE = degerlendir_model" in kaynak
    assert "SONRA = degerlendir_model" in kaynak
    assert "save_strategy': 'epoch'" in kaynak
    assert "save_total_limit': 2" in kaynak


def test_dis_islemler_izin_bayraklariyla_kapalidir_ve_token_sadece_secrettendir() -> None:
    kaynak = _kaynak()

    assert "EGITIM_CALISTIRMA_IZNI = False" in kaynak
    assert "HF_YUKLEME_IZNI = False" in kaynak
    assert "userdata.get('HF_TOKEN')" in kaynak
    assert "add_to_git_credential=False" in kaynak
    assert "push_to_hub" in kaynak
    assert "api.upload_file" in kaynak
    kod = "\n".join(
        hucre["source"] for hucre in _defteri_oku()["cells"] if hucre["cell_type"] == "code"
    )
    assert "ai.generate_text" not in kod
    assert "print(hf_token)" not in kod
    assert "HF_TOKEN =" not in kod


def test_python_hucreleri_sozdizimsel_olarak_gecerlidir() -> None:
    for hucre in _defteri_oku()["cells"]:
        if hucre["cell_type"] == "code" and "!pip install" not in hucre["source"]:
            ast.parse(hucre["source"])
