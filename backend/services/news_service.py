from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import re
import xml.etree.ElementTree as ET

import requests


NEWS_FEEDS = [
    ("Motor1 Türkiye", "https://tr.motor1.com/rss/articles/all/"),
    ("Oto Dünyasından", "https://www.otodunyasindan.com/rss/soneklenenler"),
    ("Oto Dünyasından Otomobil", "https://www.otodunyasindan.com/rss/otomobil"),
    ("Oto Aktüel", "https://www.otoaktuel.com.tr/rss"),
]


def fetch_news(limit=12):
    items = []
    errors = []

    for source_name, feed_url in NEWS_FEEDS:
        try:
            response = requests.get(
                feed_url,
                headers={"User-Agent": "BABUL/1.0 (+local-news-reader)"},
                timeout=8,
            )
            response.raise_for_status()
            items.extend(_parse_rss(response.content, source_name))
        except Exception as exc:
            errors.append({"source": source_name, "error": str(exc)})

    items = sorted(items, key=lambda item: item["publishedSort"], reverse=True)
    for item in items:
        item.pop("publishedSort", None)

    return {
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "sources": [source_name for source_name, _ in NEWS_FEEDS],
        "items": items[:limit],
        "errors": errors,
    }


def _parse_rss(content, source_name):
    root = ET.fromstring(content)
    parsed = []

    for item in root.findall(".//item"):
        title = _text(item, "title")
        link = _text(item, "link")
        description = _text(item, "description")
        published_raw = _text(item, "pubDate") or _text(item, "date")
        published_sort, published = _parse_date(published_raw)
        image_url = _find_image(item, description)

        if not title or not link:
            continue

        parsed.append({
            "source": source_name,
            "title": title,
            "url": link,
            "summary": _clean_summary(description),
            "imageUrl": image_url,
            "publishedAt": published,
            "publishedSort": published_sort,
        })

    return parsed


def _text(node, tag_name):
    found = node.find(tag_name)
    if found is None or found.text is None:
        return ""
    return found.text.strip()


def _find_image(item, description):
    for child in item:
        tag = _strip_namespace(child.tag)
        if tag in ("enclosure", "content", "thumbnail"):
            url = child.attrib.get("url") or child.attrib.get("href")
            media_type = child.attrib.get("type", "")
            if url and (tag != "enclosure" or media_type.startswith("image/") or _looks_like_image(url)):
                return url.strip()

    image_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', description or "", re.IGNORECASE)
    if image_match:
        return image_match.group(1).strip()

    return ""


def _strip_namespace(tag):
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _looks_like_image(url):
    return bool(re.search(r"\.(jpg|jpeg|png|webp|gif)(\?|$)", url or "", re.IGNORECASE))


def _parse_date(value):
    if not value:
        now = datetime.now(timezone.utc)
        return now, ""

    try:
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed, parsed.isoformat()
    except (TypeError, ValueError):
        now = datetime.now(timezone.utc)
        return now, value


def _clean_summary(value):
    if not value:
        return ""

    try:
        text = ET.fromstring(f"<root>{value}</root>").itertext()
        return " ".join(part.strip() for part in text if part.strip())[:240]
    except ET.ParseError:
        return value.strip()[:240]
