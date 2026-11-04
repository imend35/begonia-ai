"""Begonia AI Gradio arayüzü."""
import gradio as gr
from araclar import hesapla, konaklama_ucreti, oda_bilgisi, rehberde_ara
from konuk_talepleri import KATEGORILER, DURUMLAR, giris_yap, talep_olustur, talepleri_listele, durum_guncelle
from proje import ASISTAN_ADI, KIMLIK_METNI, KURUM_ADI

def sohbet_yaniti(mesaj):
    return "Lütfen bir mesaj yazın." if not mesaj.strip() else f"{ASISTAN_ADI} henüz eğitim ve resmî veri entegrasyonu aşamasına geçmedi. Doğrulanmamış bilgi paylaşamam."

with gr.Blocks(title=ASISTAN_ADI) as demo:
    gr.Markdown(f"# {ASISTAN_ADI}\n{KURUM_ADI} için Türkçe resepsiyon asistanı başlangıç arayüzü.")
    with gr.Tab("Sohbet"):
        mesaj=gr.Textbox(label="Mesajınız"); cikti=gr.Textbox(label="Yanıt")
        mesaj.submit(sohbet_yaniti, mesaj, cikti)
    with gr.Tab("Rehber / RAG"):
        sorgu=gr.Textbox(label="Rehber sorgusu"); sonuc=gr.Textbox(label="Sonuç")
        sorgu.submit(rehberde_ara, sorgu, sonuc)
    with gr.Tab("Ajan"):
        girdi=gr.Textbox(label="Araç girdisi")
        with gr.Row():
            h=gr.Button("Hesapla"); o=gr.Button("Oda bilgisi"); u=gr.Button("Konaklama ücreti")
        arac_sonuc=gr.Textbox(label="Araç sonucu")
        h.click(hesapla,girdi,arac_sonuc); o.click(oda_bilgisi,girdi,arac_sonuc); u.click(konaklama_ucreti,girdi,arac_sonuc)
    with gr.Tab("Konuk Talep Yönetimi"):
        gr.Markdown("Önce Supabase Auth kullanıcınızla giriş yapın.")
        token=gr.State(""); uid=gr.State(""); ad=gr.State("")
        with gr.Row():
            email=gr.Textbox(label="E-posta"); parola=gr.Textbox(label="Parola",type="password")
        giris=gr.Button("Giriş yap",variant="primary"); giris_sonuc=gr.Textbox(label="Oturum",interactive=False)
        giris.click(giris_yap,[email,parola],[giris_sonuc,token,uid,ad])
        gr.Markdown("### Yeni talep")
        baslik=gr.Textbox(label="Başlık"); kategori=gr.Dropdown(KATEGORILER,value="Teknik",label="Kategori"); aciklama=gr.Textbox(label="Açıklama",lines=3)
        kaydet=gr.Button("Taslak kaydet",variant="primary"); islem=gr.Textbox(label="İşlem sonucu",interactive=False)
        kaydet.click(talep_olustur,[token,uid,ad,baslik,aciklama,kategori],islem)
        yenile=gr.Button("Listeyi yenile")
        tablo=gr.Dataframe(headers=["No","Başlık","Kategori","Durum","Oluşturan","Oluşturulma","Ret gerekçesi"],datatype=["str"]*7,interactive=False)
        yenile.click(talepleri_listele,token,tablo)
        gr.Markdown("### Durum güncelle")
        talep_id=gr.Textbox(label="Talep no"); durum=gr.Dropdown(DURUMLAR,value="onay_bekliyor",label="Yeni durum"); ret=gr.Textbox(label="Ret gerekçesi")
        guncelle=gr.Button("Durumu güncelle"); guncelle_sonuc=gr.Textbox(label="Sonuç",interactive=False)
        guncelle.click(durum_guncelle,[token,talep_id,durum,ret],guncelle_sonuc)
    gr.Markdown(f"## Kimlik metni\n\n{KIMLIK_METNI}")
if __name__ == "__main__":
    demo.launch()
