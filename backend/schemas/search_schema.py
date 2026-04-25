def parse_int(value, default=None):
    if value in (None, ""):
        return default
    try:
        return int(str(value).replace(".", "").strip())
    except (TypeError, ValueError):
        return default


def parse_list(value):
    if value in (None, ""):
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [item.strip() for item in str(value).split(",") if item.strip()]


def parse_search_payload(data):
    data = data or {}
    year = str(data.get("year", "")).strip()

    year_min = parse_int(data.get("yearMin"), parse_int(year))
    year_max = parse_int(data.get("yearMax"), parse_int(year))

    return {
        "brand": str(data.get("brand", "")).strip(),
        "model": str(data.get("model", "")).strip(),
        "year": year,
        "yearMin": year_min,
        "yearMax": year_max,
        "priceMin": parse_int(data.get("priceMin")),
        "priceMax": parse_int(data.get("priceMax")),
        "kmMin": parse_int(data.get("kmMin")),
        "kmMax": parse_int(data.get("kmMax")),
        "city": str(data.get("city", "")).strip(),
        "fuelType": str(data.get("fuelType", "")).strip(),
        "transmission": str(data.get("transmission", "")).strip(),
        "bodyType": str(data.get("bodyType", "")).strip(),
        "color": str(data.get("color", "")).strip(),
        "vehicleCondition": str(data.get("vehicleCondition", "")).strip(),
        "heavyDamage": str(data.get("heavyDamage", "")).strip(),
        "paintChange": str(data.get("paintChange", "")).strip(),
        "sources": parse_list(data.get("sources")),
        "sort": str(data.get("sort", "price_asc")).strip() or "price_asc",
    }


def validate_search_criteria(criteria):
    if not criteria.get("brand") or not criteria.get("model"):
        return "Marka ve model alanları zorunludur"
    if not criteria.get("yearMin") and not criteria.get("yearMax"):
        return "En az bir model yılı seçilmelidir"
    if criteria.get("yearMin") and criteria.get("yearMax") and criteria["yearMin"] > criteria["yearMax"]:
        return "Minimum yıl maksimum yıldan büyük olamaz"
    if criteria.get("priceMin") and criteria.get("priceMax") and criteria["priceMin"] > criteria["priceMax"]:
        return "Minimum fiyat maksimum fiyattan büyük olamaz"
    if criteria.get("kmMin") and criteria.get("kmMax") and criteria["kmMin"] > criteria["kmMax"]:
        return "Minimum km maksimum km'den büyük olamaz"
    return None
