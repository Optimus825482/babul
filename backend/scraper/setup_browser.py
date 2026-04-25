"""
Browser profil kurulum scripti — ilk kez çalıştırılır, headed modda açar.

Kullanım (VPS üzerinde Xvfb ile):
  xvfb-run --auto-servernum python -m scraper.setup_browser sahibinden

Ya da doğrudan Docker içinde:
  docker exec -it <container> xvfb-run -a python -m scraper.setup_browser sahibinden

Komut satırı argümanı yoksa varsayılan olarak sahibinden açılır.
"""

import sys
import logging
from .browser_session import BrowserSession, is_playwright_available

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s — %(message)s")
log = logging.getLogger("setup_browser")

SITE_URLS = {
    "sahibinden": "https://www.sahibinden.com/otomobil",
    "arabam": "https://www.arabam.com/ikinci-el/otomobil",
}

PAUSE_SECONDS = 90  # CAPTCHA çözmek için süre


def main():
    site_key = sys.argv[1] if len(sys.argv) > 1 else "sahibinden"
    url = SITE_URLS.get(site_key, f"https://www.{site_key}.com")

    if not is_playwright_available():
        log.error("playwright yüklü değil! pip install playwright && playwright install chromium --with-deps")
        sys.exit(1)

    log.info(f"=== Browser profil kurulumu: {site_key} ===")
    log.info(f"Profil dizinine kaydedilecek → /app/data/browser-profile/{site_key}")
    log.info(f"HEADED modda açılıyor: {url}")
    log.info(f"CAPTCHA veya challenge varsa {PAUSE_SECONDS} saniye içinde çöz.\n")

    with BrowserSession(site_key, headless=False) as session:
        session.navigate_and_wait(url, pause=PAUSE_SECONDS)

    log.info("Profil kaydedildi. Artık headless modda reuse edilecek.")
    log.info("Container'ı restart etmeye gerek yok — bir sonraki istekten itibaren aktif.")


if __name__ == "__main__":
    main()
