# 🚗 AutoScout Pro - İkinci El Araç İlan Arama Platformu

<p align="center">
  <strong>Marka, Model ve Model Yılı girerek web'deki ikinci el araç ilanlarını arayın!</strong>
</p>

---

## 📋 Özellikler

- 🔍 **Çoklu Kaynak Arama** - arabam.com ve sahibinden.com'dan aynı anda arama
- 🚗 **20+ Marka Desteği** - BMW, Mercedes, Audi, Volkswagen, Toyota, Honda ve daha fazlası
- 📊 **Detaylı İlan Bilgileri** - Fiyat, yıl, konum, tarih, resim ve detay linki
- 🎨 **Modern Arayüz** - Tailwind CSS ile responsive, kullanıcı dostu tasarım
- ⚡ **Gerçek Zamanlı** - Web scraping ile güncel ilan verileri
- 📱 **Mobil Uyumlu** - Her cihazda çalışır

---

## 🛠️ Teknolojiler

| Teknoloji | Açıklama |
|-----------|----------|
| **Python 3.8+** | Backend dili |
| **Flask** | Web framework |
| **BeautifulSoup4** | HTML parsing / Web scraping |
| **Tailwind CSS** | Frontend UI framework (CDN) |
| **Vanilla JavaScript** | Frontend interaktiflik |

---

## 🚀 Hızlı Başlangıç

### Windows

```bash
# Çift tıklayın veya terminalde çalıştırın:
start.bat
```

### Linux / Mac

```bash
chmod +x start.sh
./start.sh
```

### Manuel Kurulum

```bash
# 1. Sanal ortam oluşturun
python -m venv venv

# 2. Sanal ortamı aktifleştirin
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 3. Bağımlılıkları yükleyin
pip install -r requirements.txt

# 4. Uygulamayı başlatın
python app.py
```

### Tarayıcıda açın

```
http://localhost:5000
```

---

## 📁 Proje Yapısı

```
sercar/
├── start.bat              # Windows başlatma scripti
├── start.sh               # Linux/Mac başlatma scripti
├── README.md              # Bu dosya
│
└── backend/
    ├── app.py             # Ana Flask uygulaması + API endpoints
    ├── requirements.txt   # Python bağımlılıkları
    │
    ├── scraper/
    │   ├── __init__.py    # Scraper modülü
    │   ├── base.py        # Base scraper sınıfı
    │   ├── arabam.py      # arabam.com scraper
    │   └── sahibinden.py  # sahibinden.com scraper
    │
    └── templates/
        └── index.html     # Ana sayfa template (Flask + Tailwind)
```

---

## 🔌 API Endpoints

| Endpoint | Method | Açıklama |
|----------|--------|----------|
| `/` | GET | Ana sayfa (Web arayüzü) |
| `/api/health` | GET | Sağlık kontrolü |
| `/api/brands` | GET | Marka listesi |
| `/api/models/<marka>` | GET | Markaya göre modeller |
| `/api/years` | GET | Model yılları (2000-2026) |
| `/api/search` | POST | İlan arama |

### Arama Örneği

```bash
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{"brand": "BMW", "model": "320i", "year": "2020"}'
```

### Yanıt

```json
{
  "results": [
    {
      "id": "39746704",
      "title": "AC MOTORS/2022 ÇIKIŞ 105.000 KM...",
      "modelName": "BMW 3 Serisi 320i Sport Line",
      "price": "2.680.000 TL",
      "year": "2021",
      "location": "Antalya, Manavgat",
      "date": "17 Nisan 2026",
      "imageUrl": "https://arbstorage.mncdn.com/...",
      "detailUrl": "https://www.arabam.com/ilan/...",
      "source": "arabam.com"
    }
  ],
  "count": 1,
  "query": { "brand": "BMW", "model": "320i", "year": "2020" }
}
```

---

## 📸 Ekran Görüntüsü

### Arama Sayfası

- Marka, Model, Yıl seçimi
- Ara butonu ile web'de arama
- Sonuçlar kart şeklinde listelenir

### İlan Kartı

- Araç resmi
- İlan başlığı
- Fiyat (mavi, kalın)
- Yıl badge'i
- Konum bilgisi
- İlan tarihi
- Kaynak site badge'i
- Detay butonu → ilan sayfasına yönlendirme

---

## ⚠️ Önemli Notlar

1. **Bot Koruması**: sahibinden.com bot koruması olabilir. Bu durumda sadece arabam.com sonuçları döner.
2. **Hız Sınırlaması**: Çok sık arama yapmayın, IP'niz engellenebilir.
3. **Veri Doğruluğu**: İlan bilgileri ilgili siteden anlık çekilir, güncellik garanti değildir.
4. **Prototip**: Bu uygulama bir prototiptir, üretim ortamında kullanılmamalıdır.

---

## 📄 Lisans

Bu proje eğitim ve prototip amaçlıdır.

---

<p align="center">
  <strong>AutoScout Pro</strong> ile ikinci el araç ilanlarını kolayca bulun! 🚗
</p>
