from flask import Blueprint, jsonify, request

from services.news_service import fetch_news


news_bp = Blueprint("news", __name__)


@news_bp.get("/api/news")
def get_news():
    limit = request.args.get("limit", 12, type=int)
    limit = max(1, min(limit, 30))
    return jsonify(fetch_news(limit=limit))
