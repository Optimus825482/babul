"""
Scrapling-tabanlı browser session yöneticisi.
StealthySession + user_data_dir = persistent profil (cookie, fingerprint, cf_clearance).

İlk kurulum (VPS üzerinde, headed mode):
  docker exec -it <container> python -m scraper.setup_browser sahibinden
"""

import os
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
]


def is_scrapling_available() -> bool:
    try:
        import scrapling  # noqa: F401
        return True
    except ImportError:
        return False


def is_profile_ready(site_key: str) -> bool:
    profile_dir = PROFILE_BASE / site_key
    return profile_dir.exists() and any(profile_dir.iterdir())


def _html_from_page(page) -> str | None:
    """Scrapling page nesnesinden ham HTML string döner."""
    for attr in ("html_content", "body", "__str__"):
        if attr == "__str__":
            return str(page)
        val = getattr(page, attr, None)
        if val:
            return str(val)
    return None


class BrowserSession:
    """
    Scrapling StealthySession wrapper — persistent profil desteğiyle.

    with BrowserSession("sahibinden") as s:
        html = s.fetch("https://www.sahibinden.com/...")
    """

    def __init__(self, site_key: str, headless: bool = True, solve_cloudflare: bool = True):
        self.site_key = site_key
        self.headless = headless
        self.solve_cloudflare = solve_cloudflare
        self.profile_dir = PROFILE_BASE / site_key
        self._session = None
        self.log = logging.getLogger(f"BrowserSession.{site_key}")

    def __enter__(self):
        if not is_scrapling_available():
            raise RuntimeError(
                "scrapling yüklü değil — requirements.txt'te 'scrapling[all]>=0.4.7' olmalı, "
                "Dockerfile'da 'scrapling install --force' çalıştırılmalı"
            )

        self.profile_dir.mkdir(parents=True, exist_ok=True)

        from scrapling.fetchers import StealthySession  # noqa

        self._session = StealthySession(
            headless=self.headless,
            user_data_dir=str(self.profile_dir),
            solve_cloudflare=self.solve_cloudflare,
        ).__enter__()

        self.log.info(f"StealthySession başlatıldı → {self.profile_dir}")
        return self

    def __exit__(self, *args):
        if self._session:
            try:
                self._session.__exit__(*args)
            except Exception:
                pass

    def fetch(self, url: str) -> str | None:
        """URL'den HTML döner; bot koruması veya hata varsa None."""
        try:
            page = self._session.fetch(url)
            if page is None:
                return None

            html = _html_from_page(page)
            if not html:
                return None

            html_lower = html.lower()
            if any(sig in html_lower for sig in _BOT_SIGNALS):
                self.log.warning("Bot koruması sinyali — profil yenilenmesi gerekebilir")
                return None

            return html
        except Exception as exc:
            self.log.error(f"fetch hatası ({url}): {exc}")
            return None

