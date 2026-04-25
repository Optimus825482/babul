import re


PROPERTY_ALIASES = {
    "km": ["km", "kilometre", "kilometer"],
    "fuelType": ["yakıt", "yakıt tipi", "fuel"],
    "transmission": ["vites", "vites tipi", "şanzıman", "transmission"],
    "bodyType": ["kasa", "kasa tipi", "body"],
    "enginePower": ["motor gücü", "güç", "hp", "bg"],
    "engineVolume": ["motor hacmi", "hacim", "cc"],
    "color": ["renk"],
}


def extract_number(value):
    if value in (None, ""):
        return None
    text = str(value)
    match = re.search(r"\d[\d\.]*", text)
    if not match:
        return None
    try:
        return int(match.group(0).replace(".", ""))
    except ValueError:
        return None


def normalize_text(value):
    return str(value or "").strip()


def find_property(properties, field):
    if not isinstance(properties, dict):
        return ""
    aliases = PROPERTY_ALIASES.get(field, [])
    for key, val in properties.items():
        key_norm = str(key).strip().lower()
        if any(alias in key_norm for alias in aliases):
            return normalize_text(val)
    return ""


def normalize_listing(raw, source=None):
    raw = raw or {}
    properties = raw.get("properties") or {}
    price = normalize_text(raw.get("price"))
    km = normalize_text(raw.get("km")) or find_property(properties, "km")
    fuel_type = normalize_text(raw.get("fuelType")) or find_property(properties, "fuelType")
    transmission = normalize_text(raw.get("transmission")) or find_property(properties, "transmission")
    body_type = normalize_text(raw.get("bodyType")) or find_property(properties, "bodyType")

    return {
        "id": normalize_text(raw.get("id")) or normalize_text(raw.get("detailUrl")),
        "title": normalize_text(raw.get("title")) or normalize_text(raw.get("modelName")),
        "modelName": normalize_text(raw.get("modelName")),
        "price": price,
        "priceValue": extract_number(price),
        "year": normalize_text(raw.get("year")),
        "yearValue": extract_number(raw.get("year")),
        "km": km,
        "kmValue": extract_number(km),
        "location": normalize_text(raw.get("location")),
        "city": normalize_text(raw.get("location")).split(",")[0].strip(),
        "date": normalize_text(raw.get("date")),
        "imageUrl": normalize_text(raw.get("imageUrl")),
        "imageAlt": normalize_text(raw.get("imageAlt")),
        "detailUrl": normalize_text(raw.get("detailUrl")),
        "source": source or normalize_text(raw.get("source")),
        "fuelType": fuel_type,
        "transmission": transmission,
        "bodyType": body_type,
        "enginePower": normalize_text(raw.get("enginePower")) or find_property(properties, "enginePower"),
        "engineVolume": normalize_text(raw.get("engineVolume")) or find_property(properties, "engineVolume"),
        "color": normalize_text(raw.get("color")) or find_property(properties, "color"),
        "seller": normalize_text(raw.get("seller")),
        "description": normalize_text(raw.get("description")),
        "images": raw.get("images") or [],
        "properties": properties,
        "equipment": raw.get("equipment") or [],
    }


def normalize_listings(items, source=None):
    seen = set()
    normalized = []
    for item in items or []:
        listing = normalize_listing(item, source=source)
        key = listing.get("detailUrl") or f"{listing.get('source')}:{listing.get('id')}"
        if key in seen:
            continue
        seen.add(key)
        normalized.append(listing)
    return normalized
