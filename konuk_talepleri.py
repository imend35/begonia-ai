import os
from dotenv import load_dotenv
from supabase import create_client

TABLO = "konuk_talepleri"
KATEGORILER = ("Oda", "Temizlik", "Teknik", "Misafir deneyimi", "Diger")
DURUMLAR = ("taslak", "onay_bekliyor", "yayinda", "reddedildi")

def _client(token=""):
    load_dotenv()
    client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
    if token:
        client.postgrest.auth(token)
    return client

def giris_yap(email, parola):
    try:
        result = _client().auth.sign_in_with_password({"email": email.strip(), "password": parola})
        if not result.session or not result.user:
            return "Giriş yapılamadı.", "", "", ""
        ad = (result.user.user_metadata or {}).get("full_name") or email.strip()
        return f"{ad} olarak giriş yapıldı.", result.session.access_token, str(result.user.id), ad
    except Exception as exc:
        return f"Giriş yapılamadı: {exc}", "", "", ""

def talep_olustur(token, user_id, user_name, baslik, aciklama, kategori):
    if not token:
        return "Önce giriş yapın."
    if not 3 <= len(baslik.strip()) <= 120 or not 10 <= len(aciklama.strip()) <= 2000:
        return "Başlık 3-120, açıklama 10-2000 karakter olmalıdır."
    try:
        data = {"baslik": baslik.strip(), "aciklama": aciklama.strip(), "kategori": kategori,
                "durum": "taslak", "olusturan_id": user_id, "olusturan_ad": user_name}
        result = _client(token).table(TABLO).insert(data).execute()
        return f"Talep taslak kaydedildi. No: {(result.data or [{}])[0].get('id', '')}"
    except Exception as exc:
        return f"Supabase işlemi tamamlanamadı: {exc}"

def talepleri_listele(token):
    if not token: return [["", "Önce giriş yapın.", "", "", "", "", ""]]
    try:
        rows = _client(token).table(TABLO).select("id,baslik,kategori,durum,olusturan_ad,created_at,ret_gerekcesi").order("created_at", desc=True).execute().data or []
        return [[r.get(k, "") for k in ("id","baslik","kategori","durum","olusturan_ad","created_at","ret_gerekcesi")] for r in rows]
    except Exception as exc: return [["Hata", str(exc), "", "", "", "", ""]]

def durum_guncelle(token, talep_id, durum, ret):
    if not token: return "Önce giriş yapın."
    try:
        _client(token).table(TABLO).update({"durum": durum, "ret_gerekcesi": ret.strip() or None}).eq("id", talep_id.strip()).execute()
        return "Durum güncellendi."
    except Exception as exc: return f"Supabase işlemi tamamlanamadı: {exc}"
