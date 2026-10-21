"""Sincroniza la caché local con API-Football respetando un presupuesto de consultas.

Uso (desde backend/):
    python -m scripts.api_football_sync --seasons 2025,2026 --max-requests 90
    python -m scripts.api_football_sync --seasons 2026 --details none          # solo marcadores (1 consulta por liga y temporada)
    python -m scripts.api_football_sync --seasons 2025,2026 --details recent   # + goles por minuto y tarjetas (2 consultas por partido)

Es reanudable: lo ya descargado no se vuelve a pedir; si el presupuesto se agota, retoma mañana.
Los detalles se piden de los partidos más recientes hacia atrás (los que más influyen en el análisis).
"""
from __future__ import annotations

import argparse
import sys

from app.config import load_settings
from app.providers.api_football import mapping
from app.providers.api_football.cache import RawCache
from app.providers.api_football.client import ApiFootballClient, ApiFootballError, BudgetExhausted
from app.providers.api_football.provider import DEFAULT_LEAGUES, parse_leagues
from scripts.api_football_cobertura import _load_dotenv


def sync(client: ApiFootballClient, cache: RawCache, leagues: dict, seasons: list[int], details: str,
         refresh_fixtures: bool = True) -> dict:
    stats = {"fixtures_requests": 0, "details_requests": 0, "pending_details": 0, "stopped": None}
    try:
        for lid in leagues:
            for season in seasons:
                name = f"{lid}_{season}"
                if refresh_fixtures or not cache.has("fixtures", name):
                    cache.write("fixtures", name, client.get("/fixtures", league=lid, season=season))
                    stats["fixtures_requests"] += 1
        if details == "recent":
            todo = []
            for f in cache.fixture_files():
                body = cache.read("fixtures", f.stem) or {}
                for item in body.get("response", []):
                    if mapping.status_of(item) in mapping.FINISHED:
                        fid = str(item["fixture"]["id"])
                        if not (cache.has("events", fid) and cache.has("statistics", fid)):
                            todo.append((item["fixture"]["date"], fid))
            todo.sort(reverse=True)  # más recientes primero
            stats["pending_details"] = len(todo)
            for _, fid in todo:
                if not cache.has("events", fid):
                    cache.write("events", fid, client.get("/fixtures/events", fixture=fid))
                    stats["details_requests"] += 1
                if not cache.has("statistics", fid):
                    cache.write("statistics", fid, client.get("/fixtures/statistics", fixture=fid))
                    stats["details_requests"] += 1
                stats["pending_details"] -= 1
    except BudgetExhausted as exc:
        stats["stopped"] = str(exc)
    cache.write_state(last_sync_requests=client.used, remaining_today=client.remaining_today,
                      seasons=seasons, details_mode=details)
    return stats


def main() -> int:
    _load_dotenv()
    ap = argparse.ArgumentParser()
    ap.add_argument("--seasons", required=True, help="Años separados por coma, p. ej. 2025,2026")
    ap.add_argument("--details", choices=["none", "recent"], default="none")
    ap.add_argument("--max-requests", type=int, default=90)
    ap.add_argument("--no-refresh", action="store_true", help="No volver a pedir los calendarios ya descargados")
    args = ap.parse_args()
    s = load_settings()
    leagues = parse_leagues(s.api_football_leagues or DEFAULT_LEAGUES)
    client = ApiFootballClient(s.api_football_key or "", args.max_requests)
    try:
        result = sync(client, RawCache(s.api_football_cache_dir), leagues,
                      [int(x) for x in args.seasons.split(",")], args.details, not args.no_refresh)
    except ApiFootballError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    finally:
        client.close()
    print(f"Consultas usadas: {client.used} (restantes hoy según el proveedor: {client.remaining_today})")
    print(result)
    if result["stopped"]:
        print("Se detuvo por presupuesto/límite. Vuelve a ejecutar más tarde: retoma donde quedó.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
