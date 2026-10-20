# 📋 Krarsızım - Vercel Dağıtımı & Proje Durumu El Kitabı (Handover)

Bu doküman, yeni oturumda doğrudan **Vercel Dağıtımı (Deployment)** adımından başlanabilmesi için mevcut sistem durumunu, tamamlanan geliştirmeleri ve canlıya alma adımlarını özetler.

---

## 🚀 1. Mevcut Proje Durumu
- **Durum:** Geliştirme (Faz 1-4) ve ek özellikler (anket kapatma, silme, süre kısıtı, anonim oy göçü ve çoklu kullanıcı oy izolasyonu) **%100 tamamlandı**.
- **Testler:** 35 birim testinin (`python manage.py test`) tamamı **geçti** (`OK`).
- **Canlı Mod Testi (`DEBUG=False`):** WhiteNoise entegrasyonu, manifest üretimi (`collectstatic`) ve statik varlık sunumu yerel ortamda `DEBUG=False` ile test edildi ve doğrulandı.
- **Git Durumu:** `origin/main` dalı tamamen güncel ve temiz (`clean working tree`).
- **Uzak Depo (GitHub):** [https://github.com/dirganozan/Kararsizim.git](https://github.com/dirganozan/Kararsizim.git)

---

## 🛠️ 2. Teknoloji Yığını & Mimari
- **Backend:** Python 3.12, Django 6.1.2
- **Veritabanı:** Supabase PostgreSQL (`postgresql://...` connection pooling)
- **Frontend:** HTML5, Modern Vanilla JS (ES6+), CSS3 Variables, Responsive Flex/Grid
- **Statik Dosya Sunumu:** WhiteNoise (`whitenoise.storage.CompressedManifestStaticFilesStorage`)
- **Canlı Sunucu / WSGI:** Vercel Python Serverless Runtime (`krarsizim_project/wsgi.py` -> `app = application`)

---

## 📦 3. Dağıtım Konfigürasyon Dosyaları (Hazır)
1. **`vercel.json`:**
   ```json
   {
     "version": 2,
     "builds": [
       {
         "src": "krarsizim_project/wsgi.py",
         "use": "@vercel/python",
         "config": { "maxLambdaSize": "15mb", "runtime": "python3.12" }
       },
       {
         "src": "build_files.sh",
         "use": "@vercel/static-build",
         "config": { "distDir": "staticfiles" }
       }
     ],
     "routes": [
       {
         "src": "/static/(.*)",
         "dest": "/static/$1"
       },
       {
         "src": "/(.*)",
         "dest": "krarsizim_project/wsgi.py"
       }
     ]
   }
   ```
2. **`build_files.sh`:**
   ```bash
   python3.12 -m pip install -r requirements.txt
   python3.12 manage.py collectstatic --noinput --clear
   ```
3. **`krarsizim_project/wsgi.py`:**
   `app = application` değişkeni Vercel sunucusuz fonksiyonları için tanımlandı.
4. **`requirements.txt`:**
   Gerekli tüm kütüphaneler (`Django`, `dj-database-url`, `psycopg2-binary`, `whitenoise`, `python-dotenv`) kilitlendi.

---

## 🔑 4. Vercel'e Eklenecek Ortam Değişkenleri (Environment Variables)
Yeni oturumda Vercel Dashboard üzerinden projeyi import ederken aşağıdaki değişkenler tanımlanmalıdır:

| Değişken Adı | Değer / Açıklama |
| :--- | :--- |
| `SECRET_KEY` | Güçlü rastgele Django üretim anahtarı |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `.vercel.app,127.0.0.1,localhost` |
| `DATABASE_URL` | Supabase Transaction Pooler URL (`postgresql://postgres.[ref]:[pass]@aws-0-[region].pooler.supabase.com:6543/postgres`) |
| `CSRF_TRUSTED_ORIGINS` | `https://*.vercel.app` |

---

## 📋 5. Yeni Session İçin Başlama Adımları (Next Steps)
Yeni oturumu açtığınızda asistana şu mesajı vermeniz yeterlidir:
> *"Kararsizim projesini Vercel'e deploy edeceğiz. Kodlar GitHub'da hazır. Vercel CLI veya GitHub Dashboard entegrasyonu ile canlıya alma sürecini başlatalım."*

Yeni oturumda yapılacaklar:
1. Vercel hesabı ile GitHub reposunun (`dirganozan/Kararsizim`) bağlanması.
2. Ortam değişkenlerinin Vercel'e girilmesi.
3. Build & Deploy tetiklenmesi.
4. Canlı URL üzerinden Supabase bağlantısı ve statik dosyaların son testi.
