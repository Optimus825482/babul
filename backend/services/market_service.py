from datetime import datetime, timedelta, timezone
import re
import xml.etree.ElementTree as ET

import requests


TCMB_TODAY_URL = "https://www.tcmb.gov.tr/kurlar/today.xml"
LOAN_SOURCES = [
    ("Hesapkurdu", "https://www.hesapkurdu.com/tasit-kredisi"),
    ("Hesap.com", "https://hesap.com/kredi/tasit-kredisi"),
    ("HesapMod", "https://www.hesapmod.com/finansal-hesaplamalar/tasit-kredisi-hesaplama"),
    ("KrediFast", "https://kredifast.com/index.php/sayfa/ucret-tarifeleri"),
]

_CURRENCY_META = {
    "USD": {"label": "USD/TL",      "symbol": "₺",  "unit": "$1 ="},
    "EUR": {"label": "EUR/TL",      "symbol": "₺",  "unit": "€1 ="},
    "GAU": {"label": "Gram Altın",  "symbol": "₺",  "unit": "gr"},
}


def fetch_market_snapshot():
    return {
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "rates": _fetch_tcmb_rates(),
        "loanRates": _fetch_vehicle_loan_rates(),
    }


def _fetch_yesterday_root():
    """Try to fetch the most recent past TCMB XML (skips weekends/holidays)."""
    for days_back in range(1, 5):
        d = datetime.now(timezone.utc) - timedelta(days=days_back)
        url = (
            f"https://www.tcmb.gov.tr/kurlar/"
            f"{d.strftime('%Y%m')}/{d.strftime('%d%m%Y')}.xml"
        )
        try:
            r = requests.get(url, timeout=6)
            if r.status_code == 200:
                return ET.fromstring(r.content)
        except Exception:
            continue
    return None


def _direction(current: str, previous: str) -> tuple[str, float | None]:
    """Return (direction, change_pct) comparing two string float values."""
    try:
        curr = float(current.replace(",", "."))
        prev = float(previous.replace(",", "."))
        if prev == 0:
            return "neutral", None
        pct = round(((curr - prev) / prev) * 100, 2)
        if pct > 0:
            return "up", pct
        if pct < 0:
            return "down", pct
        return "neutral", 0.0
    except (ValueError, AttributeError):
        return "neutral", None


def _fetch_tcmb_rates():
    try:
        response = requests.get(TCMB_TODAY_URL, timeout=8)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        prev_root = _fetch_yesterday_root()

        rates = []
        for code in ("USD", "EUR"):
            node = root.find(f".//Currency[@CurrencyCode='{code}']")
            if node is None:
                continue
            selling = _text(node, "ForexSelling")
            buying = _text(node, "ForexBuying")

            dir_, pct = "neutral", None
            if prev_root is not None:
                prev_node = prev_root.find(f".//Currency[@CurrencyCode='{code}']")
                if prev_node is not None:
                    dir_, pct = _direction(selling, _text(prev_node, "ForexSelling"))

            meta = _CURRENCY_META[code]
            rates.append({
                "code": code,
                "label": meta["label"],
                "symbol": meta["symbol"],
                "unit": meta["unit"],
                "buying": buying,
                "selling": selling,
                "direction": dir_,
                "change_pct": pct,
                "source": "TCMB",
            })

        gold = _fetch_gold_rate(prev_root)
        if gold:
            rates.append(gold)

        return rates
    except Exception:
        return []


def _fetch_gold_rate(prev_root=None):
    try:
        response = requests.get(
            "https://altin.doviz.com/gram-altin",
            headers={"User-Agent": "Mozilla/5.0 BABUL/1.0"},
            timeout=8,
        )
        response.raise_for_status()
        html = response.text
        bid = _extract_socket_value(html, "gram-altin", "bid")
        ask = _extract_socket_value(html, "gram-altin", "ask")
        if not bid and not ask:
            return None

        # Try to get yesterday's gold from TCMB XAU node as proxy
        dir_, pct = "neutral", None
        if prev_root is not None:
            xau = prev_root.find(".//Currency[@CurrencyCode='XAU']")
            if xau is not None:
                prev_sell = _text(xau, "ForexSelling")
                selling_val = ask or bid
                dir_, pct = _direction(selling_val, prev_sell)

        meta = _CURRENCY_META["GAU"]
        return {
            "code": "GAU",
            "label": meta["label"],
            "symbol": meta["symbol"],
            "unit": meta["unit"],
            "buying": bid,
            "selling": ask or bid,
            "direction": dir_,
            "change_pct": pct,
            "source": "Doviz.com",
        }
    except Exception:
        return None


def _fetch_vehicle_loan_rates():
    for source_name, url in LOAN_SOURCES:
        try:
            response = requests.get(
                url,
                headers={"User-Agent": "BABUL/1.0 (+local-market-reader)"},
                timeout=8,
            )
            response.raise_for_status()
            text = response.text
            rates = _extract_rates(text)
            if rates:
                return {
                    "source": source_name,
                    "url": url,
                    "rates": rates[:4],
                    "note": "Kaynak sayfadan otomatik çıkarıldı; başvuru öncesi bankadan doğrulayın.",
                }
        except Exception:
            continue

    return {
        "source": "",
        "url": "",
        "rates": [],
        "note": "Güncel taşıt kredisi oranları şu anda alınamadı.",
    }


def _extract_rates(html):
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)
    matches = re.findall(r"%\s?(\d{1,2}[,.]\d{1,2})", text)
    unique = []
    for match in matches:
        value = match.replace(",", ".")
        numeric = float(value)
        if 0.5 <= numeric <= 8 and value not in unique:
            unique.append(value)
    return [{"label": "Aylık faiz", "value": f"%{value}"} for value in unique]


def _extract_socket_value(html, key, attr):
    pattern = (
        rf'data-socket-key=["\']{re.escape(key)}["\']\s+'
        rf'data-socket-attr=["\']{re.escape(attr)}["\']>([^<]+)'
    )
    match = re.search(pattern, html)
    return match.group(1).strip() if match else ""


def _text(node, tag_name):
    found = node.find(tag_name)
    if found is None or found.text is None:
        return ""
    return found.text.strip()
