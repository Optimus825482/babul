from flask import Blueprint, jsonify

from services.market_service import fetch_market_snapshot


market_bp = Blueprint("market", __name__)


@market_bp.get("/api/market")
def get_market():
    return jsonify(fetch_market_snapshot())
