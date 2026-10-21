import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def client(settings):
    return TestClient(create_app(settings))


def test_health_and_security_headers(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"
    assert "default-src 'none'" in r.headers["content-security-policy"]


def test_source_marks_demo(client):
    s = client.get("/api/source").json()
    assert s["is_demo"] is True and s["coverage"]["clima"] is None


def test_teams_and_fixtures(client):
    assert len(client.get("/api/teams").json()["teams"]) == 20
    fx = client.get("/api/fixtures").json()
    assert fx["is_demo"] is True and len(fx["fixtures"]) == 10


def test_analysis_ok_and_errors(client):
    fx = client.get("/api/fixtures").json()["fixtures"][0]
    r = client.get("/api/analysis", params={"home": fx["home"], "away": fx["away"]})
    assert r.status_code == 200
    body = r.json()
    assert body["match"]["date"] == fx["date"] and body["prediction"]["p_home"] > 0
    assert client.get("/api/analysis", params={"home": "Aurora FC", "away": "Aurora FC"}).status_code == 422
    assert client.get("/api/analysis", params={"home": "Club Inexistente", "away": "Aurora FC"}).status_code == 404
    assert client.get("/api/analysis", params={"home": "A", "away": "Aurora FC"}).status_code == 422
    assert client.get("/api/analysis", params={"home": "Aurora FC", "away": "Cordillera", "on": "1900-01-01"}).status_code == 422
    assert client.get("/api/analysis", params={"home": "Aurora FC", "away": "Cordillera", "on": "no-es-fecha"}).status_code == 422


def test_injection_like_input_is_just_an_unknown_team(client):
    r = client.get("/api/analysis", params={"home": "'; DROP TABLE analysis_history;--", "away": "Aurora FC"})
    assert r.status_code == 404


def test_history_roundtrip(client):
    fx = client.get("/api/fixtures").json()["fixtures"][0]
    r = client.post("/api/history", json={"home": fx["home"], "away": fx["away"]})
    assert r.status_code == 201
    rec_id = r.json()["id"]
    items = client.get("/api/history").json()["items"]
    assert items[0]["id"] == rec_id and items[0]["is_demo"] is True
    full = client.get(f"/api/history/{rec_id}").json()
    assert full["analysis"]["match"]["home"] == fx["home"]
    assert client.get("/api/history/99999").status_code == 404
    assert client.post("/api/history", json={"home": "x"}).status_code == 422


def test_history_cap(settings):
    small = Settings(database_url=settings.database_url, history_max_rows=1,
                     rate_limit_per_minute=1000, write_rate_limit_per_minute=1000)
    c = TestClient(create_app(small))
    fx = c.get("/api/fixtures").json()["fixtures"][0]
    body = {"home": fx["home"], "away": fx["away"]}
    assert c.post("/api/history", json=body).status_code == 201
    assert c.post("/api/history", json=body).status_code == 507


def test_rate_limit(settings):
    tight = Settings(database_url=settings.database_url, rate_limit_per_minute=3, write_rate_limit_per_minute=1)
    c = TestClient(create_app(tight))
    codes = [c.get("/api/teams").status_code for _ in range(5)]
    assert codes[:3] == [200, 200, 200] and codes[3:] == [429, 429]
    assert c.get("/api/health").status_code == 200  # el health check no se limita
    r = c.get("/api/teams")
    assert r.status_code == 429 and "retry-after" in r.headers


def test_oversized_body_rejected(client):
    r = client.post("/api/history", content=b"x" * 20_000, headers={"content-type": "application/json"})
    assert r.status_code == 413


def test_cors_only_for_configured_origins(client):
    ok = client.get("/api/health", headers={"Origin": "http://localhost:3000"})
    bad = client.get("/api/health", headers={"Origin": "https://sitio-malicioso.example"})
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert "access-control-allow-origin" not in bad.headers


def test_docs_disabled_in_production(settings):
    prod = Settings(environment="production", database_url=settings.database_url)
    c = TestClient(create_app(prod))
    assert c.get("/docs").status_code == 404 and c.get("/openapi.json").status_code == 404


def test_validation_endpoint_flags_demo(client):
    v = client.get("/api/model/validation").json()
    assert v["status"] == "ok" and v["data_is_demo"] is True and "SINTÉTICOS" in v["warning"]


def test_seasons_and_standings(client):
    seasons = client.get("/api/seasons").json()["seasons"]
    assert seasons
    r = client.get("/api/standings", params={"season": seasons[0]})
    assert r.status_code == 200
    body = r.json()
    assert "note" in body
    pts = [t["points"] for t in body["table"]]
    assert pts == sorted(pts, reverse=True)
    assert client.get("/api/standings", params={"season": "x"}).status_code == 422
