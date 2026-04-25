import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

from data import BRAND_MODELS


CATALOG_PATH = Path(__file__).resolve().parents[1] / "data" / "vehicle_catalog.json"


def slugify(value):
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_value.lower()).strip("-")
    return slug or value.lower()


def build_seed_catalog():
    brands = []
    for brand_name, model_names in sorted(BRAND_MODELS.items()):
        brands.append({
            "name": brand_name,
            "slug": slugify(brand_name),
            "models": [
                {"name": model_name, "slug": slugify(model_name), "trims": []}
                for model_name in sorted(model_names)
            ],
        })

    return {
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "sources": ["seed"],
        "brands": brands,
    }


def load_catalog():
    if not CATALOG_PATH.exists():
        return refresh_catalog()

    with CATALOG_PATH.open("r", encoding="utf-8") as catalog_file:
        return json.load(catalog_file)


def save_catalog(catalog):
    CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CATALOG_PATH.open("w", encoding="utf-8") as catalog_file:
        json.dump(catalog, catalog_file, ensure_ascii=False, indent=2)
        catalog_file.write("\n")
    return catalog


def refresh_catalog():
    return save_catalog(build_seed_catalog())


def list_brand_names():
    catalog = load_catalog()
    return sorted(brand["name"] for brand in catalog.get("brands", []))


def find_brand(brand_or_slug):
    requested = brand_or_slug.strip().lower()
    requested_slug = slugify(brand_or_slug)

    for brand in load_catalog().get("brands", []):
        if brand["name"].lower() == requested or brand["slug"] == requested_slug:
            return brand

    return None


def list_model_names(brand_or_slug):
    brand = find_brand(brand_or_slug)
    if not brand:
        return None

    model_names = []
    for model in brand.get("models", []):
        model_names.append(model["name"])
        model_names.extend(model.get("trims", []))

    return sorted(dict.fromkeys(model_names))
