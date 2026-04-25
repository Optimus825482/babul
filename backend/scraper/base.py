# Base Scraper — Scrapling FetcherSession (TLS parmak izi) + ScraperAPI proxy desteği
import os
import time
import random
import logging
from urllib.parse import quote_plus

_SCRAPER_API_KEY = os.getenv("SCRAPER_API_KEY", "")
_SCRAPER_API_BASE = "https://api.scraperapi.com"

_UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]


def _proxy_url(original_url: str) -> str:
    if not _SCRAPER_API_KEY:
        return original_url
    return f"{_SCRAPER_API_BASE}?api_key={_SCRAPER_API_KEY}&url={quote_plus(original_url)}&render=false"


def _make_session():
    """
    Scrapling FetcherSession tercih edilir (Camoufox TLS parmak izi).
    Yüklü değilse curl_cffi, o da yoksa standart requests.
    """
    ua = random.choice(_UA_POOL)
    headers = {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Cache-Control": "no-cache",
    }

    # 1) Scrapling FetcherSession — en iyi Chrome TLS taklidi
    try:
        from scrapling.fetchers import FetcherSession
        session = FetcherSession(impersonate="chrome", stealthy_headers=True)
        session.headers.update(headers)
        return session, "scrapling"
    except Exception:
        pass

    # 2) curl_cffi fallback
    try:
        from curl_cffi import requests as cffi_requests
        chrome_ver = random.choice(["chrome110", "chrome116", "chrome120", "chrome124", "chrome131"])
        session = cffi_requests.Session(impersonate=chrome_ver)
        session.headers.update(headers)
        return session, "curl_cffi"
    except Exception:
        pass

    # 3) standart requests
    import requests
    session = requests.Session()
    session.headers.update(headers)
    return session, "requests"


class BaseScraper:
    """Tüm HTTP scraper'lar için temel sınıf."""

    SITE_URL = ""

    def __init__(self):
        self._session, self._session_type = _make_session()
        self.timeout = 35
        self.logger = logging.getLogger(self.__class__.__name__)
        self._warmed_up = False
        self.logger.info(f"HTTP backend: {self._session_type}")
        if _SCRAPER_API_KEY:
            self.logger.info("ScraperAPI proxy modu aktif")

    def _warmup(self):
        if self._warmed_up or not self.SITE_URL or _SCRAPER_API_KEY:
            self._warmed_up = True
            return
        try:
            self._session.get(self.SITE_URL, timeout=12)
            time.sleep(random.uniform(0.9, 2.0))
            self._warmed_up = True
        except Exception as e:
            self.logger.warning(f"Warmup başarısız: {e}")
            self._warmed_up = True

    def fetch(self, url: str, referer: str | None = None) -> str | None:
        """URL'den HTML çeker. ScraperAPI varsa proxy üzerinden."""
        self._warmup()
        target = _proxy_url(url)
        extra = {}
        if not _SCRAPER_API_KEY:
            extra["Referer"] = referer or self.SITE_URL or ""

        try:
            self.logger.info(f"HTTP isteği: {url}")
            if not _SCRAPER_API_KEY:
                time.sleep(random.uniform(0.5, 1.4))

            # Scrapling FetcherSession farklı çalışır
            if self._session_type == "scrapling":
                page = self._session.get(target, timeout=self.timeout)
                if page is None:
                    return None
                # Scrapling page → HTML string
                for attr in ("html_content", "body"):
                    html = getattr(page, attr, None)
                    if html:
                        return str(html)
                return str(page)
            else:
                resp = self._session.get(target, timeout=self.timeout, headers=extra)
                resp.raise_for_status()
                resp.encoding = "utf-8"
                return resp.text

        except Exception as e:
            status = getattr(getattr(e, "response", None), "status_code", "?")
            self.logger.error(f"HTTP hatası ({status}): {url}")
            return None

    def parse(self, html):
        raise NotImplementedError

    def search(self, **kwargs):
        raise NotImplementedError
