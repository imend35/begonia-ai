"""Begonia AI için değişmeyecek proje kimliği ve gerçek veri yapılandırması."""

from pathlib import Path

ASISTAN_ADI = "Begonia AI"
KURUM_ADI = "Begonvil Otel"
KAPSAM = "Türkçe otel resepsiyon asistanı"
TABAN_MODEL = "Qwen/Qwen2.5-1.5B-Instruct"

VERI_DIZINI = Path(__file__).resolve().parent / "data"
REHBER_DOSYASI = VERI_DIZINI / "rehber.pdf"
ODALAR_DOSYASI = VERI_DIZINI / "odalar.csv"
TEST_SORULARI_DOSYASI = VERI_DIZINI / "test_sorulari.csv"
ODA_TABLOSU_SUTUNLARI = (
    "oda_tipi",
    "kapasite",
    "metrekare",
    "manzara",
    "gecelik_fiyat_tl",
    "evcil_hayvan",
    "oda_sayisi",
)
CHROMA_DIZINI = "chroma_db"
PROJE_DOSYALARI = {
    "yapilandirma": "proje.py",
    "araclar": "araclar.py",
    "arayuz": "app.py",
    "rehber": REHBER_DOSYASI,
    "odalar": ODALAR_DOSYASI,
    "test_sorulari": TEST_SORULARI_DOSYASI,
}

# Benim kullanım ve eğitim sürecimde aynı kalacak temel kimlik metnim.
KIMLIK_METNI = f"""Sen {KURUM_ADI} için çalışan {ASISTAN_ADI} adlı Türkçe otel resepsiyon asistanısın.
Görevin konuklara yalnızca resmî otel rehberinde ve sağlanan verilerde bulunan bilgilerle yardımcı olmaktır.
Rehberde veya sağlanan verilerde bulunmayan oda, fiyat, kampanya, kural, hizmet ya da rezervasyon bilgisini uydurma.
Bilgi bulunmadığında bunu açıkça belirt ve resmî resepsiyonla iletişime geçilmesini öner.
Yanıtlarını Türkçe, nazik ve kısa tut."""

# Benim cevap sonu işaretim proje gereksiniminde belirtilmediği için boş kalır.
CEVAP_SONU_ISARETI = ""
