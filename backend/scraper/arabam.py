# Arabam.com Scraper - İkinci el araç ilanlarını çeker (Tüm ilanlar + Detaylar)
import re
import time
from bs4 import BeautifulSoup
from .base import BaseScraper
from .browser_session import BrowserSession, is_playwright_available, is_profile_ready


class ArabamScraper(BaseScraper):
    """arabam.com'dan ikinci el araç ilanlarını çeken scraper"""
    
    SITE_URL   = "https://www.arabam.com"
    BASE_URL   = "https://www.arabam.com"
    SEARCH_URL = "https://www.arabam.com/ikinci-el"

    def _fetch_with_browser(self, url: str) -> str | None:
        if not is_playwright_available():
            self.logger.warning("Playwright kurulu degil; arabam.com HTTP fallback kapali")
            return None
        if not is_profile_ready("arabam"):
            self.logger.warning("Arabam browser profili hazir degil; setup_browser.py calistirilmali")
            return None
        try:
            with BrowserSession("arabam", headless=True) as session:
                html = session.fetch(url)
                if html:
                    self.logger.info("Browser session ile sayfa alindi")
                return html
        except Exception as exc:
            self.logger.warning(f"Browser session basarisiz: {exc}")
            return None

    def fetch(self, url: str, referer: str | None = None) -> str | None:
        return self._fetch_with_browser(url)
    
    def search(self, brand, model, year):
        """
        Arabam.com'da araç ilanı arar - TÜM SAYFALARI tarar
        
        Args:
            brand (str): Marka (örn: "BMW")
            model (str): Model (örn: "320i") 
            year (str): Model yılı (örn: "2020")
        
        Returns:
            list: Bulunan ilanların listesi (tüm detaylar dahil)
        """
        all_listings = []
        page = 1
        max_pages = 5  # Maksimum 5 sayfa tara (100 ilan)
        
        while page <= max_pages:
            search_text = f"{brand} {model}"
            url = f"{self.SEARCH_URL}?searchText={search_text.replace(' ', '+')}&sort=price"
            url += f"&yearMin={year}&yearMax={year}"
            
            if page > 1:
                url += f"&page={page}"
            
            self.logger.info(f"Arabam.com sayfa {page} taranıyor: {url}")
            
            html = self.fetch(url)
            if not html:
                self.logger.warning(f"Sayfa {page} içeriği alınamadı")
                break
            
            listings = self.parse(html, year)
            
            if not listings:
                self.logger.info(f"Sayfa {page}'de ilan bulunamadı, tarama durduruluyor")
                break
            
            all_listings.extend(listings)
            self.logger.info(f"Sayfa {page}: {len(listings)} ilan bulundu (Toplam: {len(all_listings)})")
            
            # Aynı ilanlar tekrar gelirse dur
            if len(listings) < 20:
                break
            
            page += 1
            time.sleep(1)  # Rate limiting
        
        # Her ilanın detay sayfasını çek
        detailed_listings = []
        for i, listing in enumerate(all_listings):
            if listing.get('detailUrl'):
                detail = self.fetch_detail(listing['detailUrl'])
                if detail:
                    listing.update(detail)
                if i > 0 and i % 5 == 0:
                    time.sleep(0.5)  # Rate limiting
            detailed_listings.append(listing)
        
        self.logger.info(f"Toplam {len(detailed_listings)} ilan detaylı olarak çekildi")
        return detailed_listings
    
    def parse(self, html, year_filter=None):
        """
        HTML sayfasını parse ederek ilanları çıkarır
        
        Args:
            html (str): Sayfa HTML içeriği
            year_filter (str): Yıl filtresi (opsiyonel)
        
        Returns:
            list: Parse edilen ilanlar
        """
        soup = BeautifulSoup(html, 'lxml')
        listings = []
        
        # İlan satırlarını bul
        rows = soup.select('tr.listing-list-item')
        self.logger.info(f"Sayfada {len(rows)} ilan satırı bulundu")
        
        for row in rows:
            try:
                listing = self._parse_listing_row(row)
                if listing:
                    listings.append(listing)
            except Exception as e:
                self.logger.warning(f"İlan parse hatası: {str(e)}")
                continue
        
        return listings
    
    def _parse_listing_row(self, row):
        """Tek bir ilan satırını detaylı parse eder"""
        listing = {}
        
        # İlan ID
        listing['id'] = row.get('data-imp-id', '')
        
        # İlan linki ve detay URL'si
        link_tag = row.select_one('a[href*="/ilan/"]')
        if link_tag:
            href = link_tag.get('href', '')
            listing['detailUrl'] = f"{self.BASE_URL}{href}" if href.startswith('/') else href
        else:
            listing['detailUrl'] = ''
        
        # Resim URL - hem src hem data-src (lazy load)
        img_tag = row.select_one('img.listing-image')
        if not img_tag:
            img_tag = row.select_one('img')
        
        if img_tag:
            # Lazy-load data-src varsa onu kullan (daha yüksek kalite)
            data_src = img_tag.get('data-src', '')
            src = img_tag.get('src', '')
            
            # Eğer src placeholder/noimage ise, data-src kullan
            if data_src and ('noImage' in src or 'noimage' in src):
                listing['imageUrl'] = data_src
            elif src:
                listing['imageUrl'] = src
            elif data_src:
                listing['imageUrl'] = data_src
            else:
                listing['imageUrl'] = ''
            
            # Resim URL'sini büyük boyuta çevir
            if listing['imageUrl']:
                listing['imageUrl'] = listing['imageUrl'].replace('_240x180', '_800x600')
                listing['imageUrl'] = listing['imageUrl'].replace('_160x120', '_800x600')
            
            # Alt text
            listing['imageAlt'] = img_tag.get('alt', '')
        else:
            listing['imageUrl'] = ''
            listing['imageAlt'] = ''
        
        # TD hücrelerinden veri çek
        tds = row.select('td')
        
        # TD[1] - Model adı
        if len(tds) > 1:
            model_div = tds[1].select_one('div.listing-text-new')
            listing['modelName'] = model_div.get_text(strip=True) if model_div else tds[1].get_text(strip=True)
        else:
            listing['modelName'] = ''
        
        # TD[2] - İlan başlığı
        if len(tds) > 2:
            title_div = tds[2].select_one('div.listing-text-new')
            listing['title'] = title_div.get_text(strip=True) if title_div else tds[2].get_text(strip=True)
        else:
            listing['title'] = listing.get('modelName', '')
        
        # TD[3] - Yıl
        if len(tds) > 3:
            year_text = tds[3].get_text(strip=True)
            year_match = re.search(r'\b(19\d{2}|20\d{2})\b', year_text)
            listing['year'] = year_match.group(1) if year_match else ''
        else:
            listing['year'] = ''
        
        # TD[4] - Fiyat
        if len(tds) > 4:
            price_span = tds[4].select_one('span.listing-price')
            if price_span:
                listing['price'] = price_span.get_text(strip=True)
            else:
                price_text = tds[4].get_text(strip=True)
                if 'TL' in price_text or any(c.isdigit() for c in price_text):
                    listing['price'] = price_text
                else:
                    listing['price'] = ''
        else:
            listing['price'] = ''
        
        # TD[5] - Tarih
        if len(tds) > 5:
            listing['date'] = tds[5].get_text(strip=True)
        else:
            listing['date'] = ''
        
        # TD[6] - Konum
        if len(tds) > 6:
            location_text = tds[6].get_text(strip=True)
            # Temizle - sadece şehir/ilçe bilgisi al
            # "İstanbulBağcılarKarşılaştır..." -> "İstanbul, Bağcılar"
            loc_spans = tds[6].select('span[title]')
            if loc_spans:
                location_parts = [s.get_text(strip=True) for s in loc_spans if s.get_text(strip=True)]
                listing['location'] = ', '.join(location_parts[:2])  # İl, İlçe
            else:
                # Manuel parsing
                clean = re.sub(r'(Karşılaştır|Favori|Gizle|Göster|Ekle|Çıkar).*', '', location_text)
                listing['location'] = clean.strip()[:50]
        else:
            listing['location'] = ''
        
        # Kaynak
        listing['source'] = 'arabam.com'
        
        # Zorunlu alan kontrolü
        if not listing.get('id') and not listing.get('detailUrl'):
            return None
        
        return listing
    
    def fetch_detail(self, detail_url):
        """
        İlan detay sayfasını çeker - tüm özellikleri alır
        
        Args:
            detail_url (str): İlan detay sayfası URL'si
        
        Returns:
            dict: Detay bilgileri
        """
        try:
            html = self.fetch(detail_url)
            if not html:
                return {}
            
            soup = BeautifulSoup(html, 'lxml')
            detail = {}
            
            # === TÜM RESİMLER ===
            images = []
            # Ana görsel
            main_img = soup.select_one('.swiper-slide img, #bigImage, .detail-image img')
            if main_img:
                src = main_img.get('src', '') or main_img.get('data-src', '')
                if src:
                    images.append(src.replace('_800x600', '_1200x900'))
            
            # Galeri resimleri
            gallery_imgs = soup.select('.swiper-slide img, .thumbnail-list img, [class*="gallery"] img')
            for img in gallery_imgs:
                src = img.get('src', '') or img.get('data-src', '')
                if src and src not in images and 'noImage' not in src:
                    images.append(src.replace('_240x180', '_800x600'))
            
            if images:
                detail['images'] = images[:10]  # Maksimum 10 resim
            
            # === AÇIKLAMA ===
            desc_div = soup.select_one('.description, #tab-description, [class*="description"]')
            if desc_div:
                detail['description'] = desc_div.get_text(strip=True)[:2000]
            
            # === TEKNİK ÖZELLİKLER ===
            properties = {}
            
            # Özellik tablosu
            prop_rows = soup.select('.properties-table tr, .property-list tr, [class*="property"] tr, .detail-table tr')
            for row in prop_rows:
                cells = row.select('td, th')
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True)
                    val = cells[1].get_text(strip=True)
                    if key and val:
                        properties[key] = val
            
            # Alternatif: div bazlı özellikler
            if not properties:
                prop_items = soup.select('[class*="property-item"], [class*="feature-item"], .detail-property')
                for item in prop_items:
                    label = item.select_one('[class*="label"], [class*="name"]')
                    value = item.select_one('[class*="value"], [class*="data"]')
                    if label and value:
                        properties[label.get_text(strip=True)] = value.get_text(strip=True)
            
            if properties:
                detail['properties'] = properties
            
            # === DONANIM ÖZELLİKLERİ ===
            equipment = []
            eq_items = soup.select('[class*="equipment"] li, [class*="feature"] li, [class*="donanim"] li')
            for item in eq_items:
                text = item.get_text(strip=True)
                if text and len(text) < 50:
                    equipment.append(text)
            
            if equipment:
                detail['equipment'] = equipment[:30]
            
            # === KM BİLGİSİ ===
            km_text = soup.get_text()
            km_match = re.search(r'([\d.]+)\s*km', km_text, re.IGNORECASE)
            if km_match:
                detail['km'] = km_match.group(1) + ' km'
            
            # === YAKIT TİPİ ===
            fuel_match = re.search(r'(Benzin|Dizel|Hybrid|Elektrik|LPG)', km_text, re.IGNORECASE)
            if fuel_match:
                detail['fuelType'] = fuel_match.group(1)
            
            # === VİTES ===
            gear_match = re.search(r'(Otomatik|Manuel|Yarı Otomatik)', km_text, re.IGNORECASE)
            if gear_match:
                detail['transmission'] = gear_match.group(1)
            
            # === MOTOR GÜCÜ ===
            hp_match = re.search(r'(\d+)\s*(hp|HP|Hp|bg|BG|Bm)', km_text)
            if hp_match:
                detail['enginePower'] = hp_match.group(1) + ' HP'
            
            # === RENK ===
            color_match = re.search(r'(Beyaz|Siyah|Gri|Kırmızı|Mavi|Lacivert|Gümüş|Bordo|Yeşil|Turuncu|Kahverengi|Bej|Altın|Mor)', km_text)
            if color_match:
                detail['color'] = color_match.group(1)
            
            # === SATICI BİLGİSİ ===
            seller = soup.select_one('[class*="seller"] a, [class*="gallery-name"], [class*="dealer"]')
            if seller:
                detail['seller'] = seller.get_text(strip=True)
            
            # === TELEFON ===
            phone_match = re.search(r'0\s*(\d{3})\s*(\d{3})\s*(\d{2})\s*(\d{2})', km_text)
            if phone_match:
                detail['phone'] = phone_match.group(0)
            
            return detail
            
        except Exception as e:
            self.logger.warning(f"Detay çekme hatası ({detail_url}): {str(e)}")
            return {}
