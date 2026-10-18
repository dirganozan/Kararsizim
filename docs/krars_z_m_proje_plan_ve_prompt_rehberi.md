# Proje Dokümanı ve Geliştirme Rehberi: Krarsızım

Bu doküman, **Krarsızım** web uygulamasının geliştirilmesi sürecinde yapay zeka asistanına (Antigravity) rehberlik etmek üzere hazırlanmış kapsamlı bir sistem mimarisi ve faz planıdır.

---

## 1. Proje Özeti ve Amacı
* **Proje Adı:** Krarsızım
* **Amaç:** Kullanıcıların günlük hayatta kararsız kaldıkları konularda (Örn: *"Bugün sinemaya mı gitsem yoksa restorana mı?"*) topluluğa danışarak hızlıca anket oluşturabildiği ve diğer kullanıcıların bu anketleri oylayabildiği sosyal bir karar verme platformu.
* **Hedef:** İlk aşamada aşırı karmaşık yapılardan kaçınarak, hızlı çalışan, temiz kodlanmış bir MVP (Minimum Viable Product / Prototip) ortaya çıkarmak.

---

## 2. Temel Kurallar ve İş Mantığı (Business Logic)
1. **Akış ve Keşif:** Platformda "takip etme / arkadaş ekleme" mekanizması **yoktur**. Ana sayfada oluşturulan tüm anketler kronolojik olarak (en yeniden en eskiye) herkes tarafından görülür.
2. **Yetkilendirme ve Misafir Kullanımı:**
   * **Üye Olmayan (Anonim) Kullanıcılar:** Tüm anketleri görebilir ve **oy kullanabilirler**. (Tekrarlı oyları engellemek için tarayıcı `localStorage` veya Django `session_key` / çerez (cookie) kontrolü yapılacaktır).
   * **Üye Olan Kullanıcılar:** Anketleri görebilir, oy kullanabilir ve **yeni anket oluşturabilirler**.
3. **Kayıt ve Gizlilik:**
   * Kayıt olurken **Kullanıcı Adı (Username)**, **E-posta (Email)** ve **Parola (Password)** zorunludur.
   * Anket kartlarında sadece anketi oluşturan kişinin **kullanıcı adı** görünür; e-posta adresi kesinlikle gizli tutulur ve arayüzde paylaşılmaz.
4. **Anket Kuralları:**
   * Bir anket 1 soru metni ve **en az 2, en fazla 5** seçenekten oluşmalıdır.
   * Oy verildikten sonra ilgili anketteki seçeneklerin oy oranları yüzdelik (%) ve görsel çubuk (progress bar) olarak anında (sayfa yenilenmeden - AJAX/Fetch ile) gösterilmelidir.

---

## 3. Teknoloji Yığını (Tech Stack)
* **Backend:** Python 3.x, Django (Monolitik yapı - Django Template Engine + JSON Endpoints).
* **Veritabanı:** Supabase (PostgreSQL). Bağlantı için `psycopg2-binary` ve `dj-database-url` kullanılacak.
* **Frontend:** Ayrı bir JS framework'ü (React, Vue vb.) **kullanılmayacak**. Aynı repo içerisinde Django Templates, semantic HTML5, modern CSS3 ve Vanilla JavaScript (`fetch` API) kullanılacak.
* **Deployment:** Vercel (Serverless Python/Django yapılandırması, statik dosyalar için `whitenoise`).

---

## 4. Arayüz (UI) ve Deneyim (UX) Tasarım Rehberi
* **Hedef Kitle:** Gençler ve dinamik internet kullanıcıları (Gen-Z / Millennials).
* **Tema:** Açık arka planlı (Light Mode odaklı), ferah, nefes alan tasarım.
* **Renk Paleti (Öneri):**
  * *Arka Plan:* Çok açık kırık beyaz / gri (`#F8FAFC` veya `#F4F4F6`)
  * *Kart Arka Planı:* Saf Beyaz (`#FFFFFF`)
  * *Ana Vurgu Rengi (Primary):* Canlı Elektrik Moru / İndigo (`#6366F1` veya `#7C3AED`)
  * *İkincil Vurgu Rengi (Secondary/Accent):* Enerjik Mercan / Pembe (`#EC4899` veya `#FF5757`) ve Neon Turkuaz (`#06B6D4`)
  * *Metin:* Koyu Antrasit (`#0F172A`)
* **Tasarım Dili:** Yuvarlatılmış köşeler (`border-radius: 16px`), hafif gölgeler veya modern *neobrutalism* esintili ince belirgin çerçeveler, tıklama hissi veren mikro animasyonlu butonlar, modern tipografi (`Inter` veya `Plus Jakarta Sans` fontu).

---

## 5. Veritabanı Şeması (Modeller)
1. **User (Django Auth User):**
   * `username` (Benzersiz, görünür)
   * `email` (Benzersiz, gizli)
   * `password`
2. **Poll (Anket):**
   * `id` (PK)
   * `author` (ForeignKey -> User)
   * `question` (CharField, max 255 karakter)
   * `created_at` (DateTimeField, auto_now_add=True)
3. **Option (Seçenek):**
   * `id` (PK)
   * `poll` (ForeignKey -> Poll, related_name='options')
   * `text` (CharField, max 120 karakter)
   * `vote_count` (PositiveIntegerField, default=0)
4. **VoteLog (Oylama Kaydı - Çift Oy Engelleme İçin):**
   * `poll` (ForeignKey -> Poll)
   * `user` (ForeignKey -> User, null=True, blank=True)
   * `session_key` (CharField, anonim kullanıcılar için)
   * `created_at` (DateTimeField)

---

## 6. Adım Adım Geliştirme Fazları (Antigravity Promptları)

> **Kullanım Talimatı:** Aşağıdaki fazları sırasıyla kopyalayıp Antigravity'e yapıştırarak projeyi adım adım inşa ettirebilirsin. Bir faz tamamen çalışmadan diğerine geçme.

### FAZ 1: Proje Kurulumu, Supabase Bağlantısı ve Kullanıcı Sistemi
**Antigravity'e Verilecek Prompt:**
> "Bu dokümandaki 'Krarsızım' projesi için **Faz 1**'i başlatıyoruz.
> 1. Django proje iskeletini (`krarsizim_project` ve `core` uygulaması) oluştur.
> 2. `.env` dosyasından `DATABASE_URL` okuyarak Supabase PostgreSQL bağlantısını yapacak `settings.py` yapılandırmasını kur (`python-dotenv` ve `dj-database-url` kullan).
> 3. Kullanıcı kayıt (Sign Up), giriş (Login) ve çıkış (Logout) işlemlerini oluştur. Kayıt formunda `username`, `email` ve `password` zorunlu olsun. E-posta adresinin benzersiz (unique) olduğundan emin ol.
> 4. Tasarım rehberine uygun olarak (açık arka plan, canlı renkler, genç işi modern tasarım) bir `base.html` (Navbar'da logo, giriş/kayıt veya kullanıcı adı/çıkış butonları) ve giriş/kayıt sayfalarını HTML/CSS ile hazırla."

---

### FAZ 2: Veritabanı Modelleri ve Anket Oluşturma (2-5 Seçenek Kuralı)
**Antigravity'e Verilecek Prompt:**
> "Şimdi **Faz 2**'ye geçiyoruz.
> 1. `Poll`, `Option` ve `VoteLog` modellerini `core/models.py` içerisinde oluştur ve migration işlemlerini tanımla.
> 2. Sadece giriş yapmış kullanıcıların erişebileceği (`@login_required`) bir 'Anket Oluştur' sayfası veya modalı tasarla.
> 3. Bu formda soru başlığı ve varsayılan olarak 2 seçenek input'u gelsin. Kullanıcı Vanilla JavaScript ile '+ Seçenek Ekle' butonuna basarak en fazla 5 seçeneğe kadar input ekleyebilsin, 2'nin altına düşemesin.
> 4. Backend tarafında da seçenek sayısının **en az 2, en fazla 5** olduğunu doğrula (validation). Kaydedilen anketin yazarını (`request.user`) ata."

---

### FAZ 3: Ana Sayfa Akışı ve Dinamik Oylama Mekanizması (Üyeliksiz Oy Dahil)
**Antigravity'e Verilecek Prompt:**
> "Şimdi **Faz 3**'e geçiyoruz.
> 1. Ana sayfada (`index.html`) tüm anketleri en yeniden en eskiye doğru şık kartlar halinde listele. Her kartta sadece yazarın `@kullanici_adi`, oluşturulma zamanı, soru ve seçenekler görünsün (e-posta asla görünmesin).
> 2. Hem üye olanların hem de üye olmayan (anonim) ziyaretçilerin oy verebileceği bir JSON endpoint (`/api/poll/<id>/vote/`) yaz.
> 3. Üye olmayanlar için Django `session.session_key` (veya ek olarak `localStorage`), üyeler için `request.user` kullanarak bir ankete birden fazla oy verilmesini engelle.
> 4. Kullanıcı bir seçeneğe tıkladığında Vanilla JS (`fetch`) ile arka plana istek atılsın. Sayfa yenilenmeden ilgili anketin seçenekleri canlı renkli yüzdelik barlara (progress bar) dönüşsün ve toplam oy sayısı güncellensin."

---

### FAZ 4: UI/UX Cilalama ve Vercel Deployment Hazırlığı
**Antigravity'e Verilecek Prompt:**
> "Şimdi son aşama olan **Faz 4**'e geçiyoruz.
> 1. Arayüzü gözden geçir: Mobil uyumluluğu (responsive tasarım), buton geçiş efektlerini, oy verildikten sonra oluşan progress bar animasyonlarını ve boş durum (henüz anket yoksa gösterilecek ekran) tasarımlarını iyileştir.
> 2. Projeyi Vercel üzerinde çalıştırmak için gerekli olan `vercel.json`, `build_files.sh` (statik dosyalar ve `whitenoise` ayarları) ve `requirements.txt` dosyalarını eksiksiz şekilde oluştur.
> 3. `wsgi.py` dosyasını Vercel'in gerektirdiği `app = application` formatına uygun hale getir."