# Base Scraper - Tüm scraper'lar için temel sınıf
import requests
from bs4 import BeautifulSoup
import logging

class BaseScraper:
    """Tüm site scraper'ları için temel sınıf"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
        })
        self.timeout = 15
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def fetch(self, url):
        """URL'den HTML içeriğini çeker"""
        try:
            self.logger.info(f"İstek gönderiliyor: {url}")
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            response.encoding = 'utf-8'
            return response.text
        except requests.exceptions.Timeout:
            self.logger.error(f"Timeout hatası: {url}")
            return None
        except requests.exceptions.ConnectionError:
            self.logger.error(f"Bağlantı hatası: {url}")
            return None
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"HTTP hatası ({e.response.status_code}): {url}")
            return None
        except Exception as e:
            self.logger.error(f"Beklenmeyen hata ({type(e).__name__}): {str(e)}")
            return None
    
    def parse(self, html):
        """HTML içeriğini parse eder - alt sınıflarda override edilmeli"""
        raise NotImplementedError("parse() metodu alt sınıfta implement edilmeli")
    
    def search(self, **kwargs):
        """Arama yapar - alt sınıflarda override edilmeli"""
        raise NotImplementedError("search() metodu alt sınıfta implement edilmeli")
