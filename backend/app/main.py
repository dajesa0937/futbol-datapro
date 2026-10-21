"""API de Fútbol DataPro (FastAPI)."""
from __future__ import annotations

from datetime import date, timedelta
from datetime import date as Date
from functools import lru_cache

from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.analytics.analysis import AnalysisError, analyze_match
from app.config import Settings, load_settings
from app.db import HistoryFull, HistoryStore
from app.engine import validation
from app.providers import build_provider
from app.providers.base import ProviderError
from app.schemas import Competition
from app.security import BodySizeLimitMiddleware, RateLimitMiddleware, SecurityHeadersMiddleware



TeamName = Annotated[str, Query(min_length=2, max_length=80)]


class SaveRequest(BaseModel):
    home: str = Field(min_length=2, max_length=80)
    away: str = Field(min_length=2, max_length=80)
    date: Date | None = None


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()
    docs = None if settings.is_production else "/docs"
    app = FastAPI(title="Fútbol DataPro API", version="0.1.0", docs_url=docs,
                  redoc_url=None, openapi_url=None if settings.is_production else "/openapi.json")

    # Orden: el último añadido es el más externo.
    app.add_middleware(BodySizeLimitMiddleware)
    app.add_middleware(RateLimitMiddleware, per_minute=settings.rate_limit_per_minute,
                       write_per_minute=settings.write_rate_limit_per_minute, trust_proxy=settings.trust_proxy)
    app.add_middleware(CORSMiddleware, allow_origins=list(settings.cors_origins),
                       allow_methods=["GET", "POST"], allow_headers=["Content-Type"], allow_credentials=False)
    app.add_middleware(SecurityHeadersMiddleware)

    try:
        provider = build_provider(settings)
    except ProviderError as exc:
        raise RuntimeError(f"No se pudo iniciar el proveedor de datos: {exc}") from exc
    store = HistoryStore(settings.database_url, settings.history_max_rows)
    matches = provider.matches()
    fixtures = provider.fixtures()
    cache: dict = {}

    def source_dict() -> dict:
        info = provider.info()
        return {"name": info.name, "kind": info.kind, "is_demo": info.is_demo,
                "updated_at": info.updated_at.isoformat()}

    def run_analysis(home: str, away: str, on: date) -> dict:
        today = date.today()
        if on < date(2000, 1, 1) or on > today + timedelta(days=400):
            raise HTTPException(422, "Fecha fuera de rango.")
        try:
            return analyze_match(matches, home, away, on, source_dict())
        except AnalysisError as exc:
            msg = str(exc)
            raise HTTPException(404 if msg.startswith("Equipo") else 422, msg) from exc

    def default_date(home: str, away: str) -> date:
        for f in fixtures:
            if f.home == home and f.away == away:
                return f.date
        return date.today()

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    @app.get("/api/source")
    def source():
        info = provider.info()
        return info.model_dump(mode="json")

    @app.get("/api/seasons")
    def seasons():
        names = {f.season for f in fixtures} | {m.season for m in matches if m.competition == Competition.LIGA}
        return {"seasons": sorted(names, reverse=True)}

    @app.get("/api/standings")
    def standings(season: Annotated[str, Query(min_length=2, max_length=40)], on: date | None = None):
        """Tabla de la Liga calculada SOLO con los partidos cargados de esa temporada (antes de `on`).
        Si la fuente no trae la temporada completa, la tabla es parcial: se informa `matches_counted`."""
        rows: dict[str, dict] = {}
        counted = 0
        for m in matches:
            if m.competition != Competition.LIGA or m.season != season or (on and m.date >= on):
                continue
            counted += 1
            for team, gf, ga in ((m.home, m.home_goals, m.away_goals), (m.away, m.away_goals, m.home_goals)):
                r = rows.setdefault(team, {"team": team, "played": 0, "points": 0, "gf": 0, "ga": 0})
                r["played"] += 1; r["gf"] += gf; r["ga"] += ga
                r["points"] += 3 if gf > ga else 1 if gf == ga else 0
        table = sorted(rows.values(), key=lambda r: (-r["points"], -(r["gf"] - r["ga"]), -r["gf"], r["team"]))
        for i, r in enumerate(table, 1):
            r["position"] = i
        return {"season": season, "matches_counted": counted, "table": table,
                "note": "Calculada con los partidos cargados; puede diferir de la tabla oficial (desempates, partidos pendientes o ausentes)."}

    @app.get("/api/teams")
    def teams():
        return {"teams": provider.teams()}

    @app.get("/api/fixtures")
    def list_fixtures():
        return {"fixtures": [f.model_dump(mode="json") for f in sorted(fixtures, key=lambda f: (f.date, f.kickoff or ""))],
                "is_demo": provider.info().is_demo}

    @app.get("/api/analysis")
    def analysis(home: TeamName, away: TeamName, on: date | None = None):
        return run_analysis(home, away, on or default_date(home, away))

    @app.get("/api/model/validation")
    def model_validation():
        if "validation" not in cache:
            official = [m for m in matches if m.competition in (Competition.LIGA, Competition.COPA, Competition.INTERNACIONAL)]
            result = validation.walk_forward(official)
            result["data_is_demo"] = provider.info().is_demo
            if result["data_is_demo"]:
                result["warning"] = ("Validado sobre datos SINTÉTICOS: comprueba que el código funciona, "
                                     "no el rendimiento sobre fútbol real.")
            cache["validation"] = result
        return cache["validation"]

    @app.post("/api/history", status_code=201)
    def save_history(req: SaveRequest):
        result = run_analysis(req.home, req.away, req.date or default_date(req.home, req.away))
        try:
            rec_id = store.save(result)
        except HistoryFull as exc:
            raise HTTPException(507, str(exc)) from exc
        return {"id": rec_id}

    @app.get("/api/history")
    def list_history(limit: int = Query(default=50, ge=1, le=200)):
        return {"items": store.list(limit)}

    @app.get("/api/history/{rec_id}")
    def get_history(rec_id: int):
        rec = store.get(rec_id)
        if rec is None:
            raise HTTPException(404, "Análisis no encontrado")
        return rec

    return app


@lru_cache
def _default_app() -> FastAPI:
    return create_app()


def __getattr__(name: str):  # `uvicorn app.main:app` crea la app solo cuando se pide
    if name == "app":
        return _default_app()
    raise AttributeError(name)
