# Sahibinden.com Scraper - İkinci el araç ilanlarını çeker
import re
import time
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from .base import BaseScraper
from .browser_session import BrowserSession, is_playwright_available, is_profile_ready


class SahibindenScraper(BaseScraper):
    """sahibinden.com'dan ikinci el araç ilanlarını çeken scraper"""
    
    SITE_URL   = "https://www.sahibinden.com"
    BASE_URL   = "https://www.sahibinden.com"
    SEARCH_URL = "https://www.sahibinden.com/otomobil"
    
    def _fetch_with_browser(self, url: str) -> str | None:
        if not is_playwright_available():
            self.logger.warning("Playwright kurulu degil; sahibinden.com HTTP fallback kapali")
            return None
        if not is_profile_ready("sahibinden"):
            self.logger.warning("Sahibinden browser profili hazir degil; setup_browser.py calistirilmali")
            return None

        def run_browser_fetch():
            with BrowserSession("sahibinden", headless=True) as session:
                return session.fetch(url)

        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                html = executor.submit(run_browser_fetch).result()
            if html:
                self.logger.info("Browser session ile sayfa alindi")
            return html
        except Exception as exc:
            self.logger.warning(f"Browser session basarisiz: {exc}")
            return None

    def fetch(self, url: str, referer: str | None = None) -> str | None:
        return self._fetch_best(url)

    def _fetch_best(self, url: str) -> str | None:
        if not is_playwright_available():
            self.logger.warning("Playwright kurulu degil; sahibinden.com HTTP fallback kapali")
            return None
        if not is_profile_ready("sahibinden"):
            self.logger.warning("Sahibinden browser profili hazir degil; setup_browser.py calistirilmali")
            return None
        return self._fetch_with_browser(url)

    def search(self, brand, model, year):
        """
        sahibinden.com'da araç ilanı arar
        
        Args:
            brand (str): Marka (örn: "BMW")
            model (str): Model (örn: "320i")
            year (str): Model yılı (örn: "2020")
        
        Returns:
            list: Bulunan ilanların listesi
        """
        brand_slug = brand.lower().replace(' ', '-')
        model_slug = model.lower().replace(' ', '-')
        
        # Farklı URL formatlarını dene
        urls = [
            f"{self.SEARCH_URL}/{brand_slug}-{model_slug}?a251_max={year}&a251_min={year}",
            f"{self.SEARCH_URL}?query_text_mf={brand}+{model}&a251_max={year}&a251_min={year}",
        ]
        
        all_listings = []

        for url in urls:
            self.logger.info(f"sahibinden.com'da arama yapılıyor: {url}")

            try:
                html = self._fetch_best(url)
                if not html:
                    self.logger.warning("Sayfa içeriği alınamadı")
                    continue
                
                # Bot koruması kontrolü
                if any(x in html.lower() for x in ['captcha', 'cloudflare', 'koruma', 'ray id', 'blocked']):
                    self.logger.warning("Bot koruması tespit edildi - sahibinden.com atlanıyor")
                    return []
                
                listings = self.parse(html, year)
                all_listings.extend(listings)
                
                if listings:
                    break  # İlk çalışan URL'den sonuç geldiyse diğerini deneme
                    
            except Exception as e:
                self.logger.warning(f"sahibinden.com scrape hatası: {str(e)}")
                continue
        
        # Detayları çek
        detailed = []
        for i, listing in enumerate(all_listings):
            if listing.get('detailUrl'):
                detail = self.fetch_detail(listing['detailUrl'])
                if detail:
                    listing.update(detail)
                if i > 0 and i % 5 == 0:
                    time.sleep(0.5)
            detailed.append(listing)
        
        self.logger.info(f"sahibinden.com'dan toplam {len(detailed)} ilan bulundu")
        return detailed
    
    def parse(self, html, year_filter=None):
        """
        HTML sayfasını parse ederek ilanları çıkarır
        """
        soup = BeautifulSoup(html, 'lxml')
        listings = []
        
        # sahibinden.com listing item'ları - farklı seçici desenleri
        selectors = [
            'tr.searchResultsItem',
            'tr[class*="searchResultsItem"]',
            'tbody tr[class*="searchResults"]',
            '[class*="searchResultsItem"]',
            'tr[data-id]',
        ]
        
        items = []
        for selector in selectors:
            items = soup.select(selector)
            if items:
                self.logger.info(f"sahibinden.com: {selector} ile {len(items)} ilan bulundu")
                break
        
        if not items:
            self.logger.warning("sahibinden.com'da ilan satırı bulunamadı")
            return []
        
        for item in items:
            try:
                listing = self._parse_listing_item(item)
                if listing:
                    if year_filter and listing.get('year') and listing.get('year') != year_filter:
                        continue
                    listings.append(listing)
            except Exception as e:
                self.logger.warning(f"İlan parse hatası: {str(e)}")
                continue
        
        return listings
    
    def _parse_listing_item(self, item):
        """Tek bir ilan öğesini detaylı parse eder"""
        listing = {
            'id': '',
            'title': '',
            'modelName': '',
            'price': '',
            'year': '',
            'location': '',
            'date': '',
            'imageUrl': '',
            'detailUrl': '',
            'source': 'sahibinden.com'
        }
        
        # İlan ID
        listing['id'] = item.get('data-id', '')
        
        # İlan linki
        link_selectors = [
            'a[class*="classifiedTitle"]',
            'a[href*="/ilan/"]',
            'a[href*="/otomobil/"]',
            'td a[href*="/"]',
        ]
        for sel in link_selectors:
            link = item.select_one(sel)
            if link:
                href = link.get('href', '')
                if href and len(href) > 5:
                    listing['detailUrl'] = f"{self.BASE_URL}{href}" if href.startswith('/') else href
                    listing['title'] = link.get_text(strip=True)
                    break
        
        # Resim
        img = item.select_one('img')
        if img:
            src = img.get('src', '') or img.get('data-src', '')
            listing['imageUrl'] = src
            if img.get('alt'):
                listing['imageAlt'] = img.get('alt')
        
        # Fiyat
        price_tag = item.select_one('[class*="price"]')
        if price_tag:
            listing['price'] = price_tag.get_text(strip=True)
        
        # Model adı
        model_tag = item.select_one('[class*="model"]')
        if model_tag:
            listing['modelName'] = model_tag.get_text(strip=True)
        
        # Yıl
        text = item.get_text()
        year_match = re.search(r'\b(19\d{2}|20\d{2})\b', text)
        if year_match:
            # İlk 4 haneli sayı genelde yıl
            all_years = re.findall(r'\b(19\d{2}|20\d{2})\b', text)
            listing['year'] = all_years[0] if all_years else ''
        
        # Konum
        loc_tag = item.select_one('[class*="location"], [class*="city"]')
        if loc_tag:
            listing['location'] = loc_tag.get_text(strip=True)
        
        # Tarih
        date_match = re.search(r'\d{1,2}\s+(Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kasım|Aralık)\s+\d{4}', text)
        if date_match:
            listing['date'] = date_match.group(0)
        
        if not listing.get('detailUrl') and not listing.get('id'):
            return None
        
        return listing
    
    def fetch_detail(self, detail_url):
        """İlan detay sayfasını çeker"""
        try:
            html = self._fetch_best(detail_url)
            if not html:
                return {}
            
            soup = BeautifulSoup(html, 'lxml')
            detail = {}
            
            # Resimler
            images = []
            for img in soup.select('.classifiedDetail .thumb img, [class*="gallery"] img, [class*="photo"] img'):
                src = img.get('src', '') or img.get('data-src', '')
                if src and 'logo' not in src.lower() and 'icon' not in src.lower():
                    images.append(src)
            if images:
                detail['images'] = images[:10]
            
            # Açıklama
            desc = soup.select_one('#classifiedDescription, [class*="description"]')
            if desc:
                detail['description'] = desc.get_text(strip=True)[:2000]
            
            # Özellikler
            properties = {}
            for row in soup.select('.classifiedInfoList li, [class*="property"] li, [class*="attribute"] li'):
                cells = row.select('span, div')
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True)
                    val = cells[1].get_text(strip=True)
                    if key and val:
                        properties[key] = val
            if properties:
                detail['properties'] = properties
            
            return detail
            
        except Exception as e:
            self.logger.warning(f"sahibinden.com detay hatası: {str(e)}")
            return {}
