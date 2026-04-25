import pytest

from app import create_app
from extensions import db


@pytest.fixture()
def client(tmp_path):
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'test.db'}",
    })
    with app.app_context():
        db.create_all()
    return app.test_client()


def test_health_endpoint_returns_ok(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "OK"
    assert payload["version"]


def test_filter_options_include_sources_and_vehicle_facets(client):
    response = client.get("/api/filters/options")

    assert response.status_code == 200
    payload = response.get_json()
    assert "brands" in payload
    assert "years" in payload
    assert {"arabam.com", "sahibinden.com"}.issubset(set(payload["sources"]))
    assert "fuelTypes" in payload
    assert "transmissions" in payload


def test_listings_endpoint_supports_empty_pagination(client):
    response = client.get("/api/listings?page=1&pageSize=12")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["results"] == []
    assert payload["pagination"]["page"] == 1
    assert payload["pagination"]["pageSize"] == 12
    assert payload["pagination"]["total"] == 0
