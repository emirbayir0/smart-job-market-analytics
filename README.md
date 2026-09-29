# ⚡ Smart Market & Skill Analytics Automation Platform

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Playwright](https://img.shields.io/badge/Playwright-Automated_Scraping-45BA4B?style=for-the-badge&logo=playwright&logoColor=white)](https://playwright.dev/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Interactive_Dashboard-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![SQLite](https://img.shields.io/badge/SQLite-SQLAlchemy_ORM-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)

**Smart Market & Skill Analytics Platform**, web sitelerinden teknoloji iş ilanlarını ve piyasa verilerini otomatik toplayan, Yapay Zeka (Gemini API / Rule-based NLP) ile ilan metinlerinden en çok aranan becerileri ve kıdem seviyelerini çıkaran, Telegram üzerinden anlık bildirim atan ve verileri etkileşimli bir dashboard üzerinde görselleştiren uçtan uca bir otomasyon sistemidir.

---

## 🌟 Öne Çıkan Özellikler

- **🤖 Akıllı Veri Kazıma & ETL Hattı:** Dynamic web sayfalarından veri toplama, temizleme ve mükerrer kayıt önleme (Deduplication).
- **🧠 Yapay Zeka (AI) Destekli Beceri Çıkarımı:** Gemini API ile ilanlardan otomatik yetenek (*Python, Docker, FastAPI vb.*), kıdem (*Junior, Mid, Senior*) ve çalışma tipi (*Uzaktan, Hibrit*) çıkarımı.
- **📊 Etkileşimli Streamlit Dashboard:** 
  - Canlı KPI metrikleri (Toplam ilan, uzaktan çalışma oranı vb.)
  - Plotly ile teknolojilerin popülerlik grafiği ve çalışma tipi dağılımı.
  - Anlık arama, beceri filtreleme ve ilan listeleme.
  - Manuel kazıma başlatma ve canlı otomasyon logları.
- **⏰ Arka Plan Zamanlayıcısı (APScheduler):** Belirlenen periyotlarda otomatik veri kazıma.
- **💬 Telegram Bot Bildirim Sistemi:** Yeni ve yüksek öncelikli ilanlarda anlık mesaj bildirimi.
- **🐳 Docker & Docker Compose Desteği:** Tek komutla konteyner üzerinde çalıştırma.

---

## 🛠️ Mimari Şema

```
[ Web Sayfaları ] ──(Playwright / Scraper)──> [ ETL Engine & NLP Parser ]
                                                     │
                                             (Gemini AI API)
                                                     │
[ Telegram Bot ] <──(APScheduler / Alert)──── [ SQLite Database ] ────> [ Streamlit UI ]
```

---

## 🚀 Kurulum & Çalıştırma

### 1. Yerel Ortam (Local)

1. Gerekli kütüphaneleri yükleyin:
   ```bash
   pip install -r requirements.txt
   ```

2. Veritabanını ilklendirin ve Scraper'ı çalıştırın:
   ```bash
   python database.py
   python scraper.py
   ```

3. Streamlit Dashboard'u başlatın:
   ```bash
   streamlit run app.py
   ```
   Tarayıcınızda `http://localhost:8501` adresine gidin.

### 2. Automated Testleri Çalıştırma

```bash
pytest test_project.py -v
```

### 3. Docker ile Çalıştırma

```bash
docker-compose up --build -d
```

---

## 📂 Proje Dizin Yapısı

```
smart_market_tracker/
├── app.py                 # Streamlit Web Dashboard & UI
├── scraper.py             # Playwright / BeautifulSoup Kazıma Hattı
├── database.py            # SQLAlchemy Modelleri & Veritabanı Mantığı
├── ai_analyzer.py         # Gemini API & NLP Beceri Çıkarma Servisi
├── notifier.py            # Telegram Bildirim Motoru
├── scheduler.py           # APScheduler Arka Plan Görev Yöneticisi
├── config.py              # Sistem Ayarları & Ortam Değişkenleri
├── test_project.py        # PyTest Otomatik Test Dosyası
├── requirements.txt       # Python Bağımlılıkları
├── Dockerfile             # Docker Konfigürasyonu
└── docker-compose.yml     # Docker Compose Yapılandırması
```
