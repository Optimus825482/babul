"""
Browser profil kurulum scripti.
Cloudflare cözer, sahibinden.com'a otomatik login yapar, profili kaydeder.

Kullanim:
  SAHIBINDEN_EMAIL=mail@example.com SAHIBINDEN_PASSWORD=sifren \
  docker exec -it <container> xvfb-run -a python -m scraper.setup_browser sahibinden
"""

import os
import sys
import time
import logging
from scraper.browser_session import BrowserSession, is_scrapling_available, PROFILE_BASE

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s - %(message)s")
log = logging.getLogger("setup_browser")

SITE_URLS = {
    "sahibinden": "https://www.sahibinden.com/otomobil",
    "arabam": "https://www.arabam.com/ikinci-el/otomobil",
}

LOGIN_URL = "https://secure.sahibinden.com/login"


def _sahibinden_login(session: BrowserSession) -> bool:
    email = os.getenv("SAHIBINDEN_EMAIL", "")
    password = os.getenv("SAHIBINDEN_PASSWORD", "")

    if not email or not password:
        log.warning("SAHIBINDEN_EMAIL / SAHIBINDEN_PASSWORD tanimli degil. Login atlanıyor.")
        return False

    log.info(f"Login deneniyor: {email}")

    try:
        ctx = session._session
        pages = getattr(ctx, "pages", [])
        if not pages:
            log.error("Acik sayfa yok")
            return False

        pg = pages[-1]
        pg.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=20000)
        time.sleep(2)

        # Email
        for sel in ['input[name="username"]', 'input[type="email"]', '#user_email', '[placeholder*="posta"]']:
            try:
                pg.fill(sel, email, timeout=3000)
                log.info(f"Email alani bulundu: {sel}")
                break
            except Exception:
                continue

        time.sleep(0.3)

        # Sifre
        for sel in ['input[name="password"]', 'input[type="password"]', '#user_password']:
            try:
                pg.fill(sel, password, timeout=3000)
                log.info(f"Sifre alani bulundu: {sel}")
                break
            except Exception:
                continue

        time.sleep(0.3)

        # Submit
        for sel in ['button[type="submit"]', 'input[type="submit"]', '[class*="login-btn"]', '[class*="giris"]']:
            try:
                pg.click(sel, timeout=3000)
                log.info("Login formu gonderildi")
                break
            except Exception:
                continue

        time.sleep(4)
        current_url = pg.url
        if "login" not in current_url:
            log.info(f"Login basarili! URL: {current_url}")
            return True
        else:
            log.warning(f"Login basarisiz, hala login sayfasinda: {current_url}")
            return False

    except Exception as exc:
        log.error(f"Login hatasi: {exc}")
        return False


def main():
    site_key = sys.argv[1] if len(sys.argv) > 1 else "sahibinden"
    url = SITE_URLS.get(site_key, f"https://www.{site_key}.com")

    if not is_scrapling_available():
        log.error("scrapling yuklu degil!")
        sys.exit(1)

    log.info(f"=== Browser profil kurulumu: {site_key} ===")
    log.info(f"Profil: {PROFILE_BASE / site_key}")

    with BrowserSession(site_key, headless=True, solve_cloudflare=True) as session:
        log.info(f"Sayfa aciliyor: {url}")
        html = session.fetch(url)

        if site_key == "sahibinden":
            if html is None or "sahibinden.com/login" in (html or ""):
                log.info("Login sayfasina yonlendirildi, otomatik login deneniyor...")
                login_ok = _sahibinden_login(session)
                if login_ok:
                    html = session.fetch(url)
                    if html:
                        log.info(f"Ilan sayfasi alindi ({len(html)} byte)")
                    else:
                        log.warning("Login sonrasi ilan sayfasi alinamadi")
            else:
                if html:
                    log.info(f"Sayfa alindi ({len(html)} byte)")

    log.info("Profil kaydedildi.")


if __name__ == "__main__":
    main()
