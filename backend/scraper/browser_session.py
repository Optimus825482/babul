"""
Playwright persistent context — anti-bot scraping için browser profil yöneticisi.

İlk kurulum (VPS üzerinde):
  docker exec -it <container> python -m scraper.setup_browser sahibinden

Sonraki tüm istekler kaydedilen profili (cookies + localStorage) reuse eder.
"""

import os
import time
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

PROFILE_BASE = Path(os.getenv("BROWSER_PROFILE_DIR", "/app/data/browser-profile"))

_BOT_SIGNALS = [
    "just a moment",
    "ray id",
    "cf-browser-verification",
    "enable javascript",
    "ddos-guard",
    "robot değilsiniz",
    "robot olup olmadığınızı",
    "güvenlik doğrulaması",
]


def is_playwright_available() -> bool:
    try:
        import playwright  # noqa: F401
        return True
    except ImportError:
        return False


def is_profile_ready(site_key: str) -> bool:
    """Profil dizini oluşturulmuş ve içinde veri var mı?"""
    profile_dir = PROFILE_BASE / site_key
    if not profile_dir.exists():
        return False
    # En az bir dosya varsa hazır kabul et
    return any(profile_dir.iterdir())


class BrowserSession:
    """
    Playwright persistent context wrapper.

    with BrowserSession("sahibinden") as s:
        html = s.fetch("https://www.sahibinden.com/...")
    """

    def __init__(self, site_key: str, headless: bool = True):
        self.site_key = site_key
        self.headless = headless
        self.profile_dir = PROFILE_BASE / site_key
        self._pw = None
        self._ctx = None
        self.log = logging.getLogger(f"BrowserSession.{site_key}")

    def __enter__(self):
        if not is_playwright_available():
            raise RuntimeError(
                "playwright yüklü değil — requirements.txt'e ekle ve "
                "Dockerfile'da 'playwright install chromium --with-deps' çalıştır"
            )

        self.profile_dir.mkdir(parents=True, exist_ok=True)

        from playwright.sync_api import sync_playwright  # noqa

        self._pw = sync_playwright().__enter__()
        self._ctx = self._pw.chromium.launch_persistent_context(
            str(self.profile_dir),
            headless=self.headless,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ],
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1366, "height": 768},
            locale="tr-TR",
            timezone_id="Europe/Istanbul",
            extra_http_headers={
                "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
            },
        )
        self.log.info(f"Persistent context başlatıldı → {self.profile_dir}")
        return self

    def __exit__(self, *args):
        if self._ctx:
            try:
                self._ctx.close()
            except Exception:
                pass
        if self._pw:
            try:
                self._pw.__exit__(*args)
            except Exception:
                pass

    def fetch(self, url: str, wait_seconds: float = 2.5) -> str | None:
        """URL'den HTML döner; bot koruması varsa None."""
        try:
            page = self._ctx.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            time.sleep(wait_seconds)
            html = page.content()
            page.close()

            html_lower = html.lower()
            if any(sig in html_lower for sig in _BOT_SIGNALS):
                self.log.warning("Bot koruması sinyali alındı — profil yenilenmesi gerekebilir")
                return None

            return html
        except Exception as exc:
            self.log.error(f"fetch hatası ({url}): {exc}")
            return None

    def navigate_and_wait(self, url: str, pause: float = 60.0):
        """
        Headed (görsel) modda sayfayı açar ve kullanıcıdan manuel işlem bekler.
        Profil kurulum adımı için kullanılır.
        """
        page = self._ctx.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        self.log.info(
            f"Sayfa açıldı: {url}\n"
            f"CAPTCHA / challenge varsa çöz, ardından devam edilecek ({pause}s bekleniyor)…"
        )
        time.sleep(pause)
        html = page.content()
        page.close()
        return html
