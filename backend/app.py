# BABUL - İkinci El Araç İlan Arama Platformu
# Flask Backend + Frontend (Jinja2 Templates)
# ============================================================

from flask import Flask, jsonify, request, render_template
import logging
import sys
import os

# Scraper modülünü path'e ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scraper.arabam import ArabamScraper
from scraper.sahibinden import SahibindenScraper
from scraper.normalizer import normalize_listings
from schemas.search_schema import parse_search_payload, validate_search_criteria
from config import Config
from extensions import cors, db
from routes.metadata_routes import metadata_bp
from routes.news_routes import news_bp
from routes.market_routes import market_bp

# Logging ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Scraper instance'ları
arabam_scraper = ArabamScraper()
sahibinden_scraper = SahibindenScraper()


# ============================================================
# SAYFA ROUTE'LARI (Frontend)
# ============================================================

def create_app(config_overrides=None):
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config.from_object(Config)
    if config_overrides:
        app.config.update(config_overrides)

    cors.init_app(app)
    db.init_app(app)
    app.register_blueprint(metadata_bp)
    app.register_blueprint(news_bp)
    app.register_blueprint(market_bp)
    register_routes(app)
    return app


def register_routes(app):
    @app.route('/')
    def index():
        """Ana sayfa"""
        return render_template('index.html')

    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Sağlık kontrolü endpoint'i"""
        return jsonify({
            'status': 'OK',
            'message': 'BABUL API çalışıyor',
            'version': '1.0.0'
        })

    @app.route('/api/search', methods=['POST'])
    def search_listings():
        """
        İkinci el araç ilanlarını arar

        Request Body:
            {
                "brand": "BMW",
                "model": "320i",
                "year": "2020"
            }
        """
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Request body gerekli'}), 400

        criteria = parse_search_payload(data)
        brand = criteria["brand"]
        model = criteria["model"]
        year = criteria["year"]

        # Validasyon
        validation_error = validate_search_criteria(criteria)
        if validation_error:
            return jsonify({
                'error': validation_error,
                'results': [],
                'count': 0
            }), 400

        logger.info(f"Arama isteği: {brand} {model} {year}")

        all_results = []
        errors = []

        # Arabam.com'da ara
        try:
            arabam_results = arabam_scraper.search(brand, model, year)
            all_results.extend(arabam_results)
            logger.info(f"Arabam.com'dan {len(arabam_results)} ilan bulundu")
        except Exception as e:
            error_msg = f"Arabam.com hatası: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)

        # Sahibinden.com'da ara
        try:
            sahibinden_results = sahibinden_scraper.search(brand, model, year)
            all_results.extend(sahibinden_results)
            logger.info(f"Sahibinden.com'dan {len(sahibinden_results)} ilan bulundu")
        except Exception as e:
            error_msg = f"Sahibinden.com hatası: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)

        # Sonuçları fiyata göre sırala
        all_results = normalize_listings(all_results)
        all_results = _filter_results(all_results, criteria)
        all_results = _sort_results(all_results, criteria.get("sort"))

        response = {
            'results': all_results,
            'count': len(all_results),
            'query': {
                'brand': brand,
                'model': model,
                'year': year,
                'filters': _active_filters(criteria),
            }
        }

        if errors:
            response['warnings'] = errors

        return jsonify(response)

    @app.route('/api/search/stream', methods=['GET'])
    def search_stream_sse():
        """Server-Sent Events ile arama sonuçlarını progressive olarak gönderir."""
        import json
        from flask import stream_with_context, Response as FlaskResponse

        brand = request.args.get('brand', '').strip()
        model = request.args.get('model', '').strip()
        year = request.args.get('year', '').strip()

        validation_error = validate_search_criteria({"brand": brand, "model": model, "year": year})
        if validation_error:
            def err_gen():
                yield f'data: {json.dumps({"error": validation_error})}\n\n'
                yield 'data: {"done": true}\n\n'
            return FlaskResponse(stream_with_context(err_gen()), mimetype='text/event-stream')

        def generate():
            count = 0
            # Arabam
            try:
                for result in arabam_scraper.search_stream(brand, model, year):
                    count += 1
                    payload = json.dumps(result, ensure_ascii=False)
                    yield f'data: {payload}\n\n'
            except Exception as exc:
                logger.error(f"SSE arabam hatası: {exc}")

            # Sahibinden
            try:
                for result in sahibinden_scraper.search_stream(brand, model, year):
                    count += 1
                    payload = json.dumps(result, ensure_ascii=False)
                    yield f'data: {payload}\n\n'
            except Exception as exc:
                logger.error(f"SSE sahibinden hatası: {exc}")

            yield f'data: {json.dumps({"done": True, "count": count})}\n\n'

        return FlaskResponse(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',
                'Connection': 'keep-alive',
            }
        )

    @app.route('/api/browser-status', methods=['GET'])
    def browser_status():
        """Playwright browser profil durumunu döner."""
        from scraper.browser_session import is_scrapling_available, is_profile_ready
        return jsonify({
            "playwright_available": is_scrapling_available(),
            "sahibinden_profile_ready": is_profile_ready("sahibinden"),
            "setup_command": (
                "docker exec -it <container> "
                "xvfb-run -a python -m scraper.setup_browser sahibinden"
            ),
        })

    @app.route('/api/listings', methods=['GET'])
    def get_listings():
        page = request.args.get("page", 1, type=int)
        page_size = request.args.get("pageSize", 12, type=int)
        return jsonify({
            "results": [],
            "pagination": {
                "page": page,
                "pageSize": page_size,
                "total": 0,
            },
        })


app = create_app()


def _extract_price_number(price_str):
    """Fiyat string'inden sayısal değer çıkarır (sıralama için)"""
    try:
        clean = price_str.replace('TL', '').replace('.', '').replace(',', '.').strip()
        return float(clean)
    except (ValueError, AttributeError):
        return 0


def _filter_results(results, criteria):
    filtered = []
    for item in results:
        if not _in_range(item.get("priceValue"), criteria.get("priceMin"), criteria.get("priceMax")):
            continue
        if not _in_range(item.get("kmValue"), criteria.get("kmMin"), criteria.get("kmMax")):
            continue
        if not _in_range(item.get("yearValue"), criteria.get("yearMin"), criteria.get("yearMax")):
            continue
        if not _matches_text(item.get("fuelType"), criteria.get("fuelType")):
            continue
        if not _matches_text(item.get("transmission"), criteria.get("transmission")):
            continue
        if not _matches_text(item.get("bodyType"), criteria.get("bodyType")):
            continue
        if not _matches_text(item.get("color"), criteria.get("color")):
            continue
        if not _matches_optional_text(item, criteria.get("vehicleCondition")):
            continue
        if not _matches_optional_text(item, criteria.get("paintChange")):
            continue
        if not _matches_heavy_damage(item, criteria.get("heavyDamage")):
            continue
        filtered.append(item)
    return filtered


def _in_range(value, minimum, maximum):
    if value is None:
        return True
    if minimum is not None and value < minimum:
        return False
    if maximum is not None and value > maximum:
        return False
    return True


def _matches_text(value, expected):
    if not expected:
        return True
    if not value:
        return True
    return _fold(expected) in _fold(value)


def _matches_optional_text(item, expected):
    if not expected:
        return True
    haystack = " ".join([
        str(item.get("title") or ""),
        str(item.get("description") or ""),
        " ".join(f"{key} {value}" for key, value in (item.get("properties") or {}).items()),
    ])
    if not haystack.strip():
        return True
    return _fold(expected) in _fold(haystack)


def _matches_heavy_damage(item, expected):
    if expected == "":
        return True
    haystack = " ".join([
        str(item.get("title") or ""),
        str(item.get("description") or ""),
        " ".join(f"{key} {value}" for key, value in (item.get("properties") or {}).items()),
    ])
    folded = _fold(haystack)
    if not folded:
        return True
    has_heavy_damage = "agir hasar" in folded or "ağır hasar" in haystack.lower()
    return has_heavy_damage if expected == "true" else not has_heavy_damage


def _sort_results(results, sort_key):
    if sort_key == "price_desc":
        return sorted(results, key=lambda item: item.get("priceValue") or 0, reverse=True)
    if sort_key == "km_asc":
        return sorted(results, key=lambda item: item.get("kmValue") if item.get("kmValue") is not None else 10**12)
    if sort_key == "year_desc":
        return sorted(results, key=lambda item: item.get("yearValue") or 0, reverse=True)
    return sorted(results, key=lambda item: item.get("priceValue") if item.get("priceValue") is not None else 10**12)


def _active_filters(criteria):
    hidden = {"brand", "model", "year", "yearMin", "yearMax", "sources", "sort"}
    return {key: value for key, value in criteria.items() if key not in hidden and value not in (None, "", [])}


def _fold(value):
    translation = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
    return str(value or "").translate(translation).lower()


# ============================================================
# UYGULAMA BAŞLATMA
# ============================================================

if __name__ == '__main__':
    logger.info("=" * 50)
    logger.info("BABUL Başlatılıyor...")
    logger.info("=" * 50)
    logger.info(f"📌 Uygulama: http://localhost:5000")
    logger.info(f"📌 API Health: http://localhost:5000/api/health")
    logger.info(f"📌 API Brands: http://localhost:5000/api/brands")
    logger.info("=" * 50)

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )

