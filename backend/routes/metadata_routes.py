from flask import Blueprint, jsonify, request

from data import FILTER_OPTIONS, YEARS
from services.vehicle_catalog_service import (
    list_brand_names,
    list_model_names,
    load_catalog,
    refresh_catalog,
)


metadata_bp = Blueprint("metadata", __name__)


@metadata_bp.get("/api/catalog")
def get_catalog():
    return jsonify(load_catalog())


@metadata_bp.post("/api/catalog/refresh")
def refresh_vehicle_catalog():
    if not request.host.startswith(("127.0.0.1", "localhost")):
        return jsonify({"error": "Catalog refresh is only available locally"}), 403

    catalog = refresh_catalog()
    return jsonify({
        "updatedAt": catalog["updatedAt"],
        "sources": catalog["sources"],
        "brandCount": len(catalog.get("brands", [])),
    })


@metadata_bp.get("/api/brands")
def get_brands():
    brands = list_brand_names()
    return jsonify({"brands": brands, "count": len(brands)})


@metadata_bp.get("/api/models/<brand>")
def get_models(brand):
    models = list_model_names(brand)
    if models is None:
        return jsonify({"error": f"Marka bulunamadı: {brand}", "models": []}), 404

    return jsonify({"brand": brand, "models": models, "count": len(models)})


@metadata_bp.get("/api/years")
def get_years():
    return jsonify({"years": YEARS, "count": len(YEARS)})


@metadata_bp.get("/api/filters/options")
def get_filter_options():
    return jsonify({
        "brands": list_brand_names(),
        "years": YEARS,
        **FILTER_OPTIONS,
    })
