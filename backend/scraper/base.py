# Base Scraper - Chrome TLS parmak izi taklidi ile bot korumasını geçer
import random
import time
import logging

try:
    from curl_cffi import requests as cffi_requests
    _CFFI_AVAILABLE = True
except ImportError:
    import requests as _fallback_requests
    _CFFI_AVAILABLE = False

# Chrome sürüm havuzu — TLS parmak izi için
_CHROME_VERSIONS = ["chrome110", "chrome116", "chrome120", "chrome124", "chrome131"]

_UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]


class BaseScraper:
    """Tüm scraper'lar için temel sınıf — curl_cffi ile Chrome TLS taklidi"""

    SITE_URL = ""  # Alt sınıfta tanımlanmalı

    def __init__(self):
        self._chrome_ver = random.choice(_CHROME_VERSIONS)
        self._ua = random.choice(_UA_POOL)
        self.timeout = 22
        self.logger = logging.getLogger(self.__class__.__name__)
        self._warmed_up = False

        if _CFFI_AVAILABLE:
            self._session = cffi_requests.Session(impersonate=self._chrome_ver)
        else:
            self.logger.warning("curl_cffi bulunamadı, standart requests kullanılıyor (403 riski yüksek)")
            self._session = _fallback_requests.Session()

        self._session.headers.update({
            "User-Agent": self._ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "no-cache",
        })

    def _warmup(self):
        """Ana sayfayı ziyaret ederek gerçekçi oturum / cookie oluşturur."""
        if self._warmed_up or not self.SITE_URL:
            return
        try:
            self._session.get(self.SITE_URL, timeout=12)
            time.sleep(random.uniform(0.9, 2.0))
            self._warmed_up = True
            self.logger.info(f"Warmup tamamlandı: {self.SITE_URL}")
        except Exception as e:
            self.logger.warning(f"Warmup başarısız ({self.SITE_URL}): {e}")

    def fetch(self, url: str, referer: str | None = None) -> str | None:
        """URL'den HTML içeriğini çeker."""
        self._warmup()

        extra = {}
        if referer:
            extra["Referer"] = referer
        elif self.SITE_URL:
            extra["Referer"] = self.SITE_URL

        try:
            self.logger.info(f"İstek gönderiliyor: {url}")
            time.sleep(random.uniform(0.5, 1.4))
            resp = self._session.get(url, timeout=self.timeout, headers=extra)
            resp.raise_for_status()
            resp.encoding = "utf-8"
            return resp.text
        except Exception as e:
            status = getattr(getattr(e, "response", None), "status_code", "?")
            self.logger.error(f"HTTP hatası ({status}): {url}")
            return None

    # Alt sınıflar bunları override eder
    def parse(self, html):
        raise NotImplementedError

    def search(self, **kwargs):
        raise NotImplementedError
