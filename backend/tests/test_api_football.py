"""Pruebas del adaptador API-Football con respuestas SINTÉTICAS que siguen el formato documentado.

Importante: estas pruebas verifican la lógica de mapeo y de presupuesto, NO que la API real
responda así. El formato real debe confirmarse con `scripts/api_football_cobertura.py`.
"""
import httpx
import pytest

from app.providers.api_football import mapping
from app.providers.api_football.cache import RawCache
from app.providers.api_football.client import ApiFootballClient, ApiFootballError, BudgetExhausted
from app.providers.api_football.provider import ApiFootballProvider
from app.schemas import Competition
from scripts.api_football_sync import sync


def fx(fid, status, home, away, hg, ag, date="2026-03-01T23:30:00+00:00", rnd="Apertura - 5"):
    return {"fixture": {"id": fid, "date": date, "status": {"short": status}, "referee": "Árbitro X",
                        "venue": {"name": "Estadio Z"}},
            "league": {"id": 239, "season": 2026, "round": rnd},
            "teams": {"home": {"name": home}, "away": {"name": away}},
            "goals": {"home": hg, "away": ag}}


def ev(team, minute, player="Jugador", detail="Normal Goal"):
    return {"type": "Goal", "detail": detail, "time": {"elapsed": minute}, "team": {"name": team}, "player": {"name": player}}


def stats(team, y, r):
    return {"team": {"name": team}, "statistics": [{"type": "Yellow Cards", "value": y}, {"type": "Red Cards", "value": r}]}


def test_timezone_conversion_to_bogota():
    day, hhmm = mapping.local_date_and_time("2026-03-02T01:30:00+00:00")  # 20:30 del día anterior en Bogotá
    assert str(day) == "2026-03-01" and hhmm == "20:30"


def test_map_finished_and_upcoming():
    m = mapping.map_finished(fx(1, "FT", "A", "B", 2, 1), Competition.LIGA)
    assert (m.home_goals, m.away_goals, m.season) == (2, 1, "2026 Apertura")
    assert mapping.map_finished(fx(2, "NS", "A", "B", None, None), Competition.LIGA) is None
    assert mapping.map_finished(fx(3, "PST", "A", "B", None, None), Competition.LIGA) is None
    f = mapping.map_upcoming(fx(2, "NS", "A", "B", None, None), Competition.LIGA)
    assert f is not None and f.kickoff == "18:30"


def test_events_must_match_score_else_discarded():
    m = mapping.map_finished(fx(1, "FT", "A", "B", 1, 1), Competition.LIGA)
    ok, problem = mapping.apply_events(m, [ev("A", 10), ev("B", 80)])
    assert problem is None and [g.minute for g in ok.goals] == [10, 80]
    bad, problem = mapping.apply_events(m, [ev("A", 10)])
    assert problem and bad.goals is None


def test_statistics_missing_is_reported_not_zero():
    m = mapping.map_finished(fx(1, "FT", "A", "B", 0, 0), Competition.LIGA)
    same, problem = mapping.apply_statistics(m, [stats("A", 2, 0)])
    assert problem and not same.has_cards
    done, problem = mapping.apply_statistics(m, [stats("A", 2, 0), stats("B", 3, 1)])
    assert problem is None and (done.home_yellow, done.away_red) == (2, 1)


def _handler(calls, remaining="3"):
    def handler(request: httpx.Request):
        calls.append(request.url.path)
        assert request.headers["x-apisports-key"] == "k"
        return httpx.Response(200, headers={"x-ratelimit-requests-remaining": remaining},
                              json={"errors": [], "results": 0, "response": []})
    return handler


def test_client_budget_and_errors():
    calls = []
    c = ApiFootballClient("k", max_requests=2, transport=httpx.MockTransport(_handler(calls)))
    c.get("/fixtures", league=1)
    c.get("/fixtures", league=2)
    with pytest.raises(BudgetExhausted):
        c.get("/fixtures", league=3)
    assert len(calls) == 2
    with pytest.raises(ApiFootballError):
        ApiFootballClient("")
    bad = httpx.MockTransport(lambda r: httpx.Response(200, json={"errors": {"token": "Error"}, "response": []}))
    with pytest.raises(ApiFootballError):
        ApiFootballClient("k", transport=bad).get("/fixtures")


def test_sync_is_resumable_and_provider_reads_cache(tmp_path):
    cache = RawCache(tmp_path)
    items = [fx(10, "FT", "Alfa", "Beta", 1, 0, "2026-02-01T23:00:00+00:00"),
             fx(11, "FT", "Beta", "Alfa", 2, 2, "2026-02-08T23:00:00+00:00"),
             fx(12, "NS", "Alfa", "Beta", None, None, "2026-10-30T23:00:00+00:00")]
    payloads = {"/fixtures": {"errors": [], "response": items}}
    def handler(request):
        path = request.url.path
        if path == "/fixtures":
            return httpx.Response(200, json=payloads["/fixtures"])
        fid = int(request.url.params["fixture"])
        if path == "/fixtures/events":
            r = [ev("Alfa", 30)] if fid == 10 else [ev("Beta", 5), ev("Beta", 50), ev("Alfa", 20), ev("Alfa", 70)]
            return httpx.Response(200, json={"errors": [], "response": r})
        return httpx.Response(200, json={"errors": [], "response": [stats("Alfa", 1, 0), stats("Beta", 2, 0)]})
    client = ApiFootballClient("k", max_requests=3, transport=httpx.MockTransport(handler))
    r1 = sync(client, cache, {239: Competition.LIGA}, [2026], "recent")
    assert r1["stopped"] and r1["pending_details"] > 0  # 3 consultas no alcanzan para todo
    client2 = ApiFootballClient("k", max_requests=50, transport=httpx.MockTransport(handler))
    r2 = sync(client2, cache, {239: Competition.LIGA}, [2026], "recent", refresh_fixtures=False)
    assert r2["stopped"] is None and r2["pending_details"] == 0
    prov = ApiFootballProvider(str(tmp_path), "239:liga_betplay")
    info = prov.info()
    assert info.is_demo is False and info.coverage["partidos"] == 2
    assert info.coverage["con_minutos_de_gol_pct"] == 100.0 and info.coverage["con_tarjetas_pct"] == 100.0
    assert prov.teams() == ["Alfa", "Beta"] and len(prov.fixtures()) == 1
    assert cache.read_state()["details_mode"] == "recent"
