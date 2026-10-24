# 📋 Krarsızım - Vercel Dağıtımı & Proje Durumu El Kitabı (Handover)

Bu doküman, Krarsızım projesinin **Vercel Dağıtımı (Deployment)** sürecini, canlı ortam mimarisini, yapılandırma ayrıntılarını ve erişim adreslerini özetler.

---

## 🚀 1. Canlı Dağıtım Durumu (Canlıda & Aktif)
- **Canlı Üretim URL (Production):** [https://kararsizim-bay.vercel.app](https://kararsizim-bay.vercel.app)
- **Vercel Proje Adı:** `kararsizim` (`dirgan/kararsizim`)
- **Proje ID:** `prj_Yx9nO8XIDV899BEhEcYyoLwn769r`
- **Dağıtım Durumu:** `READY` (HTTP 200 OK)
- **Erişim Koruması:** Herkese açık (SSO Deployment Protection devre dışı bırakıldı)
- **Testler:** 35 birim testinin tamamı başarıyla geçmektedir (`OK`).
- **Uzak Depo (GitHub):** [https://github.com/dirganozan/Kararsizim.git](https://github.com/dirganozan/Kararsizim.git)

---

## 🛠️ 2. Teknoloji Yığını & Mimari
- **Backend:** Python 3.12, Django 6.1.2
- **Veritabanı:** Supabase PostgreSQL (IPv4 Transaction Pooler, Port: 6543, Bölge: `eu-west-1`)
- **Frontend:** HTML5, Modern Vanilla JS (ES6+), CSS3 Değişkenleri, Responsive Tasarım
- **Statik Dosyalar (CDN):** Vercel Edge CDN (`staticfiles_build/static`) + WhiteNoise yedeklemesi
- **Sunucusuz Çalışma Zamanı (WSGI):** `@vercel/python` (Python 3.12, `krarsizim_project/wsgi.py` -> `app = application`)

---

## 📦 3. Dağıtım Dosyaları & Konfigürasyon
1. **`vercel.json`:**
   ```json
   {
     "version": 2,
     "builds": [
       {
         "src": "krarsizim_project/wsgi.py",
         "use": "@vercel/python",
         "config": {
           "maxLambdaSize": "15mb",
           "runtime": "python3.12"
         }
       },
       {
         "src": "build_files.sh",
         "use": "@vercel/static-build",
         "config": {
           "distDir": "staticfiles_build"
         }
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
   #!/bin/bash
   echo "--> Bağımlılıklar yükleniyor..."
   python3 -m pip install -r requirements.txt
   echo "--> Statik dosyalar derleniyor (collectstatic)..."
   python3 manage.py collectstatic --noinput --clear
   echo "--> Build başarıyla tamamlandı!"
   ```
3. **`krarsizim_project/settings.py`:**
   - `STATIC_ROOT = BASE_DIR / 'staticfiles_build' / 'static'`
   - `STATIC_URL = '/static/'`
   - `WHITENOISE_MANIFEST_STRICT = False`

---

## 🔑 4. Vercel Ortam Değişkenleri (Tanımlandı & Aktif)

| Değişken Adı | Değer / Amaç |
| :--- | :--- |
| `SECRET_KEY` | Üretim için güvenli rastgele 50 karakterlik Django anahtarı |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `.vercel.app,127.0.0.1,localhost` |
| `DATABASE_URL` | `postgresql://postgres.isgskfkgufccalihrzbl:[SUPABASE_PASSWORD]@aws-0-eu-west-1.pooler.supabase.com:6543/postgres` |
| `CSRF_TRUSTED_ORIGINS` | `https://*.vercel.app` |

---

## 🔍 5. Doğrulama ve Test Sonuçları
- **Ana Sayfa:** HTTP 200 OK (Mevcut anketler ve oy sayıları Supabase üzerinden dinamik olarak başarıyla render edildi).
- **Statik CSS & JS:** Vercel CDN üzerinden HTTP 200 OK ile doğru MIME tipleriyle (`text/css`, `application/javascript`) sunuluyor.
- **Kimlik Doğrulama Sayfaları:** `/login/` ve `/register/` sayfaları sorunsuz çalışmaktadır.
