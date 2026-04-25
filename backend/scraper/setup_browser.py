"""
Browser profil kurulum scripti — sahibinden.com için.
İlk kez çalıştırılır, headed modda açar; Cloudflare challenge'ı otomatik çözmeye çalışır.

Kullanım (VPS / Docker):
  docker exec -it <container> python -m scraper.setup_browser sahibinden
  # veya Xvfb gerektiren ortamlar için:
  docker exec -it <container> xvfb-run -a python -m scraper.setup_browser sahibinden
"""

import sys
import logging
from browser_session import BrowserSession, is_scrapling_available, PROFILE_BASE

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s — %(message)s")
log = logging.getLogger("setup_browser")

SITE_URLS = {
    "sahibinden": "https://www.sahibinden.com/otomobil",
    "arabam": "https://www.arabam.com/ikinci-el/otomobil",
}


def main():
    site_key = sys.argv[1] if len(sys.argv) > 1 else "sahibinden"
    url = SITE_URLS.get(site_key, f"https://www.{site_key}.com")

    if not is_scrapling_available():
        log.error(
            "scrapling yüklü değil!\n"
            "  pip install 'scrapling[all]>=0.4.7'\n"
            "  scrapling install --force"
        )
        sys.exit(1)

    log.info(f"=== Browser profil kurulumu: {site_key} ===")
    log.info(f"Profil kaydedilecek: {PROFILE_BASE / site_key}")
    log.info(f"Headless=False modda açılıyor, Cloudflare otomatik çözülmeye çalışılacak…")

    # headless=False + solve_cloudflare=True → challenge'ı gerçek tarayıcı ile çözer
    with BrowserSession(site_key, headless=False, solve_cloudflare=True) as session:
        html = session.fetch(url)
        if html:
            log.info(f"Sayfa başarıyla alındı ({len(html)} byte). Profil kaydedildi.")
        else:
            log.warning("Sayfa alınamadı — profil kaydedildi ama challenge çözülememiş olabilir.")

    log.info("Kurulum tamamlandı. Container restart gerekmez.")


if __name__ == "__main__":
    main()

