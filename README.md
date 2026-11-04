<<<<<<< HEAD
# Begonia AI

Ben, Tech Istanbul Uygulamalı Yapay Zekâ Geliştirme Bootcamp bitirme projem kapsamında Begonia AI adlı Türkçe otel resepsiyon asistanını geliştiriyorum. Bu depoda başlangıç yapılandırması, gerçek oda araçları ve ADIM 3A eğitim hazırlığı bulunur.

Begonia AI, kurgusal Begonvil Otel için tasarlanmıştır. İlerleyen aşamalarda Qwen/Qwen2.5-1.5B-Instruct modeli QLoRA ile eğitilecek; resmî otel rehberi PDF + Chroma ile RAG kapsamında kullanılacaktır. Bu aşamada model indirme, eğitim, API çağrısı veya dış servise yükleme yapılmaz.

## Klasör yapısı

```text
.
├── app.py
├── araclar.py
├── konuk_talepleri.py
├── proje.py
├── requirements.txt
├── data/
├── notebooks/
├── reports/
└── tests/
```

Ben resmî kaynak dosyalarımı aşağıdaki adlarla kullanıyorum:

- `data/rehber.pdf`
- `data/odalar.csv`
- `data/test_sorulari.csv`

Ben bu dosyalar dışında oda, fiyat, kural veya rehber bilgisi uydurmuyorum.

## Kurulum ve çalıştırma

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Temel testleri çalıştırmak için:

```bash
pytest
```

## ADIM 3A: sentetik veri ve eğitim öncesi ölçüm

Ben `egitim_verisi.py` ile yeniden üretilebilir sentetik veri hazırlıyorum. Bu betik, `data/egitim/` altında üç ayrı JSONL kümesi üretir:

- `egitim.jsonl`: 450 örnek; 150 kimlik, 150 RAG ve 150 ajan örneği içerir.
- `dogrulama.jsonl`: 60 örnek; eğitim kümesinden ayrı tutulur.
- `degerlendirme.jsonl`: Eğitim öncesi ve sonrası aynı sorularla ölçüm için 60 örnek içerir.

Ben eğitim verisini ve kontrollerini şu komutla yeniden oluşturuyorum:

```bash
python egitim_verisi.py
```

Ben şema, geçerli JSON, örnek sayısı, rehber/CSV kaynak tutarlılığı, gerçek araç sonucu ve doğrudan soru sızıntısını testlerle doğruluyorum:

```bash
python -m pytest tests -q
```

Ben `notebooks/adim_3a_egitim_hazirligi.ipynb` defterini Colab T4 ortamında hazırlık ve denetim için kullanıyorum. Hocanın örnek Colab defterine erişimim olmadığı için `messages` alanlı OpenAI/TRL tarzı JSONL biçimini varsayıyorum; bunu doğrulanmış uyumluluk olarak sunmuyorum. Örnek defter farklı bir biçim isterse yalnızca dönüştürme katmanını güncelleyeceğim.

Ben değerlendirme çıktılarımı `data/egitim/degerlendirme_cikti_sablonu.json` şablonuna ayrı kaydediyorum. Metriklerim kimlik doğruluğu, cevap işareti doğruluğu, geçerli JSON, doğru araç ve RAG doğruluğudur. Cevap sonu işareti şu anda boş olduğu için ilgili metrik işaret dayatılmadığını kontrol eder.

Ben Gemini veya başka bir dış servis kullanmıyorum. Dış servisle gerçek veri üretimi gerekirse API anahtarını koda yazmayacağım ve API çağrısından önce açık onay alacağım. Bu aşamada QLoRA eğitimi, model indirme, Hugging Face yükleme ve GGUF dönüşümü yapmıyorum.

## Konuk Talep Yönetimi

`Konuk Talep Yönetimi` sekmesi talepleri Supabase'e kaydeder, filtreler ve
durum günceller. Varsayılan olarak `guest_requests` tablosunda şu sütunları
bekler: `id`, `guest_name`, `room_number`, `request_type`, `description`,
`priority`, `status`, `created_at`.

`.env` dosyasındaki `SUPABASE_URL` ve `SUPABASE_KEY` yeterlidir. Şemanızın
tablo veya sütun isimleri farklıysa örneğin aşağıdaki değişkenleri ekleyin:

```env
SUPABASE_GUEST_REQUESTS_TABLE=konuk_talepleri
SUPABASE_GUEST_REQUESTS_GUEST_NAME_COLUMN=konuk_adi
SUPABASE_GUEST_REQUESTS_ROOM_NUMBER_COLUMN=oda_no
```
=======
# begonia-ai
>>>>>>> 444e2579be24d5848d06c42ecfee61470ccdedbf
