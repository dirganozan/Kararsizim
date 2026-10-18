# 🤔 Krarsızım - Sosyal Karar Verme Platformu

**Krarsızım**, günlük hayatta kararsız kalınan konularda (*"Bugün sinemaya mı gitsem restorana mı?"*, *"Hangi telefonu alsam?"*) topluluğa danışarak hızlıca anket oluşturulabilen ve diğer kullanıcıların bu anketleri oylayabildiği modern bir web uygulamasıdır.

---

## 🚀 Özellikler

* **Topluluk Akışı:** Takip etme zorunluluğu olmadan en yeniden en eskiye kronolojik anket keşfi.
* **Hızlı Anket Oluşturma (2-5 Seçenek):**
  * Açılır Modal (Popup) veya bağımsız sayfa üzerinden hızlıca soru ve seçenek tanımlama.
  * Dinamik seçenek ekleme/çıkarma (Vanilla JS, minimum 2 - maksimum 5 seçenek kuralı).
* **Canlı Oylama (Real-Time AJAX):**
  * Sayfa yenilenmeden tek tıkla oy kullanma (`Fetch API`).
  * Canlı animasyonlu renkli yüzdelik çubuklar (Progress Bars) ve toplam oy güncellemesi.
  * Kullanıcının tercih ettiği seçeneği belirten özel rozet ("✓ Senin Oyun").
* **Çift Oy Engelleme:**
  * Üye kullanıcılar için veritabanı seviyesinde `request.user` koruması.
  * Üye olmayan (anonim) misafir kullanıcılar için Django `session_key` ve `localStorage` koruması.
* **Gizlilik ve Güvenlik:**
  * Benzersiz e-posta ile kayıt; anketlerde ve profilde yalnızca `@kullanici_adi` görünür.
* **Modern & Duyarlı (Responsive) Tasarım:**
  * Plus Jakarta Sans tipografisi, hafif açık tema, canlı mor/mercan vurgular ve mobil uyumluluk.

---

## 🛠️ Teknoloji Yığını

* **Backend:** Python 3.12+, Django (Monolitik mimari)
* **Veritabanı:** Supabase (PostgreSQL) & SQLite (Lokal test ve geliştirme)
* **Frontend:** Django Template Engine, Semantic HTML5, Modern CSS3, Vanilla JavaScript
* **Deployment:** Vercel Serverless Python & Whitenoise

---

## 💻 Yerel Geliştirme (Local Setup)

1. **Depoyu klonlayın ve klasöre girin:**
   ```bash
   git clone https://github.com/dirganozan/Kararsizim.git
   cd Kararsizim
   ```

2. **Sanal ortamı oluşturun ve aktif edin:**
   ```bash
   python -m venv .venv
   # Windows için:
   .\.venv\Scripts\activate
   # macOS/Linux için:
   source .venv/bin/activate
   ```

3. **Bağımlılıkları yükleyin:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Ortam değişkenlerini ayarlayın:**
   `.env.example` dosyasını `.env` olarak kopyalayın ve gerekli değerleri girin:
   ```env
   SECRET_KEY=your-secret-key
   DEBUG=True
   ALLOWED_HOSTS=*
   # Supabase kullanmak için:
   DATABASE_URL=postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres
   # Boş bırakılırsa yerel SQLite (db.sqlite3) kullanılır.
   ```

5. **Veritabanı migrasyonlarını uygulayın ve statik dosyaları toplayın:**
   ```bash
   python manage.py migrate
   python manage.py collectstatic --noinput
   ```

6. **Geliştirme sunucusunu başlatın:**
   ```bash
   python manage.py runserver
   ```
   Tarayıcınızdan `http://127.0.0.1:8000/` adresine gidin.

7. **Testleri çalıştırın:**
   ```bash
   python manage.py test
   ```

---

## ☁️ Vercel Deployment Rehberi

1. GitHub deponuzu [vercel.com](https://vercel.com) hesabınıza import edin.
2. **Environment Variables** bölümüne şunları ekleyin:
   * `SECRET_KEY`: Güçlü ve rastgele bir anahtar.
   * `DEBUG`: `False`
   * `ALLOWED_HOSTS`: `*` veya `.vercel.app`
   * `DATABASE_URL`: Supabase PostgreSQL bağlantı dizeniz.
   * `CSRF_TRUSTED_ORIGINS`: `https://*.vercel.app`
3. **Deploy** butonuna basın. Projeniz otomatik olarak derlenecek ve canlıya alınacaktır!

---

## 📄 Lisans
Bu proje açık kaynaklı bir MVP prototipidir.
