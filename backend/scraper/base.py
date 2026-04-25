# Base Scraper - Tüm scraper'lar için temel sınıf
import random
import time
import requests
from bs4 import BeautifulSoup
import logging

_UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
]


class BaseScraper:
    """Tüm site scraper'ları için temel sınıf"""

    SITE_URL = ""  # Alt sınıfta tanımlanmalı (ana sayfa)

    def __init__(self):
        self.session = requests.Session()
        self._set_headers()
        self.timeout = 20
        self.logger = logging.getLogger(self.__class__.__name__)
        self._warmed_up = False

    def _set_headers(self):
        ua = random.choice(_UA_POOL)
        is_firefox = "Firefox" in ua
        self.session.headers.update({
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            **(
                {}
                if is_firefox
                else {
                    "Sec-CH-UA": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
                    "Sec-CH-UA-Mobile": "?0",
                    "Sec-CH-UA-Platform": '"Windows"',
                }
            ),
        })

    def _warmup(self):
        """Ana sayfayı ziyaret ederek gerçekçi oturum oluşturur."""
        if self._warmed_up or not self.SITE_URL:
            return
        try:
            self.session.get(self.SITE_URL, timeout=10)
            time.sleep(random.uniform(0.8, 1.8))
            self._warmed_up = True
        except Exception:
            pass

    def fetch(self, url, referer: str | None = None):
        """URL'den HTML içeriğini çeker."""
        self._warmup()

        headers = {}
        if referer:
            headers["Referer"] = referer
        elif self.SITE_URL:
            headers["Referer"] = self.SITE_URL

        try:
            self.logger.info(f"İstek gönderiliyor: {url}")
            time.sleep(random.uniform(0.4, 1.2))
            response = self.session.get(url, timeout=self.timeout, headers=headers)
            response.raise_for_status()
            response.encoding = "utf-8"
            return response.text
        except requests.exceptions.Timeout:
            self.logger.error(f"Timeout hatası: {url}")
        except requests.exceptions.ConnectionError:
            self.logger.error(f"Bağlantı hatası: {url}")
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"HTTP hatası ({e.response.status_code}): {url}")
        except Exception as e:
            self.logger.error(f"Beklenmeyen hata ({type(e).__name__}): {str(e)}")
        return None

    def parse(self, html):
        """HTML içeriğini parse eder - alt sınıflarda override edilmeli"""
        raise NotImplementedError("parse() metodu alt sınıfta implement edilmeli")

    def search(self, **kwargs):
        """Arama yapar - alt sınıflarda override edilmeli"""
        raise NotImplementedError("search() metodu alt sınıfta implement edilmeli")
