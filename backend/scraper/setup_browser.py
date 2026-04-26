"""
Browser profil kurulum + sahibinden otomatik login.

Kullanim:
  SAHIBINDEN_EMAIL=mail@example.com SAHIBINDEN_PASSWORD=sifren \
  docker exec -it <container> xvfb-run -a python -m scraper.setup_browser sahibinden
"""

import os
import sys
import time
import logging
from pathlib import Path
from scraper.browser_session import is_scrapling_available, PROFILE_BASE

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s - %(message)s")
log = logging.getLogger("setup_browser")

LISTING_URL = "https://www.sahibinden.com/otomobil"
LOGIN_URL   = "https://secure.sahibinden.com/login"


def _delete_locks(profile_dir: Path):
    for lock in ["SingletonLock", "SingletonCookie", "SingletonSocket"]:
        p = profile_dir / lock
        if p.exists():
            p.unlink(missing_ok=True)


def setup_sahibinden(profile_dir: Path):
    email    = os.getenv("SAHIBINDEN_EMAIL", "")
    password = os.getenv("SAHIBINDEN_PASSWORD", "")

    if not email or not password:
        log.error("SAHIBINDEN_EMAIL ve SAHIBINDEN_PASSWORD env var olarak tanimlanmali!")
        sys.exit(1)

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        log.error("playwright yuklu degil")
        sys.exit(1)

    profile_dir.mkdir(parents=True, exist_ok=True)
    _delete_locks(profile_dir)

    log.info(f"Playwright headless baslatiliyor → {profile_dir}")

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            str(profile_dir),
            headless=True,
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
            locale="tr-TR",
            viewport={"width": 1366, "height": 768},
        )

        page = ctx.new_page()

        # 1) Listing sayfasini ac — login redirect gelecek
        log.info(f"Aciliyor: {LISTING_URL}")
        page.goto(LISTING_URL, wait_until="domcontentloaded", timeout=30000)
        time.sleep(2)

        # 2) Login sayfasindaysak form doldur
        if "login" in page.url:
            log.info(f"Login sayfasi: {page.url}")
            log.info(f"Email dolduruluyor: {email}")

            # Email alani
            filled = False
            for sel in [
                'input[name="username"]',
                'input[type="email"]',
                '#user_email',
                'input[placeholder*="posta"]',
                'input[placeholder*="mail"]',
            ]:
                try:
                    page.fill(sel, email, timeout=4000)
                    filled = True
                    log.info(f"Email alani: {sel}")
                    break
                except Exception:
                    continue

            if not filled:
                log.error("Email alani bulunamadi. Sayfa kaynagini kontrol edin.")
                # Sayfayi kaydet
                with open("/tmp/login_page.html", "w") as f:
                    f.write(page.content())
                log.info("Sayfa /tmp/login_page.html dosyasina kaydedildi")
                ctx.close()
                return

            time.sleep(0.4)

            # Sifre alani
            for sel in [
                'input[name="password"]',
                'input[type="password"]',
                '#user_password',
            ]:
                try:
                    page.fill(sel, password, timeout=4000)
                    log.info(f"Sifre alani: {sel}")
                    break
                except Exception:
                    continue

            time.sleep(0.4)

            # Submit
            submitted = False
            for sel in [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Giriş")',
                'button:has-text("Giris")',
            ]:
                try:
                    page.click(sel, timeout=4000)
                    submitted = True
                    log.info(f"Form gonderildi: {sel}")
                    break
                except Exception:
                    continue

            if not submitted:
                page.keyboard.press("Enter")
                log.info("Enter ile form gonderildi")

            time.sleep(5)

            if "login" not in page.url:
                log.info(f"LOGIN BASARILI! URL: {page.url}")
            else:
                log.warning(f"Login basarisiz — URL: {page.url}")
                log.warning("Email/sifre yanlis olabilir veya CAPTCHA gerekiyor.")

        else:
            log.info(f"Login gerekmedi, direkt acildi: {page.url}")

        # 3) Profili kaydet
        ctx.close()

    log.info("Profil kaydedildi. Artık her arama bu session ile gidecek.")


def main():
    site_key = sys.argv[1] if len(sys.argv) > 1 else "sahibinden"
    profile_dir = PROFILE_BASE / site_key

    if not is_scrapling_available() and site_key == "sahibinden":
        # scrapling olmasa bile playwright varsa devam et
        pass

    log.info(f"=== Setup: {site_key} ===")

    if site_key == "sahibinden":
        setup_sahibinden(profile_dir)
    else:
        log.error(f"Desteklenmeyen site: {site_key}")
        sys.exit(1)


if __name__ == "__main__":
    main()
