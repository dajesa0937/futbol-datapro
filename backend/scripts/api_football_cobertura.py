"""Prueba de cobertura de API-Football para la Liga BetPlay (gasta pocas consultas).

Uso (desde backend/, con la clave en .env o en el entorno):
    python -m scripts.api_football_cobertura                 # lista ligas de Colombia y su cobertura (1 consulta)
    python -m scripts.api_football_cobertura --league 239 --season 2025   # + prueba un partido terminado (≈4 consultas)

Guarda las respuestas crudas en data/cache/api_football_raw_cobertura/ para revisarlas o enviarlas
y ajustar el mapeo. No imprime ni guarda la clave.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from app.config import load_settings
from app.providers.api_football import mapping
from app.providers.api_football.client import ApiFootballClient, ApiFootballError


def _load_dotenv() -> None:
    env = Path(".env")
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.split("#")[0].strip())


def main() -> int:
    _load_dotenv()
    ap = argparse.ArgumentParser()
    ap.add_argument("--league", type=int)
    ap.add_argument("--season", type=int)
    ap.add_argument("--max-requests", type=int, default=8)
    args = ap.parse_args()
    settings = load_settings()
    raw = Path("data/cache/api_football_raw_cobertura")
    client = ApiFootballClient(settings.api_football_key or "", args.max_requests, raw_dir=raw)
    try:
        leagues = client.get("/leagues", country="Colombia")
        print(f"\nLigas devueltas para Colombia: {leagues.get('results')}")
        for item in leagues.get("response", []):
            lg = item.get("league", {})
            print(f"\n[{lg.get('id')}] {lg.get('name')} ({lg.get('type')})")
            for s in item.get("seasons", [])[-4:]:
                cov = s.get("coverage", {})
                fx = cov.get("fixtures", {})
                print(f"  temporada {s.get('year')}: eventos={fx.get('events')} alineaciones={fx.get('lineups')} "
                      f"stats_partido={fx.get('statistics_fixtures')} stats_jugador={fx.get('statistics_players')} "
                      f"posiciones={cov.get('standings')} lesiones={cov.get('injuries')}")
        if args.league and args.season:
            fixtures = client.get("/fixtures", league=args.league, season=args.season)
            body = fixtures.get("response", [])
            done = [i for i in body if mapping.status_of(i) in mapping.FINISHED]
            print(f"\nLiga {args.league} temporada {args.season}: {len(body)} partidos, {len(done)} terminados.")
            if done:
                sample = done[-1]
                fid = sample["fixture"]["id"]
                ev = client.get("/fixtures/events", fixture=fid)
                st = client.get("/fixtures/statistics", fixture=fid)
                print(f"Partido de muestra {fid}: eventos={ev.get('results')} bloques_estadisticas={st.get('results')}")
        print(f"\nConsultas usadas: {client.used}. Restantes hoy según el proveedor: {client.remaining_today}")
        print(f"Respuestas crudas guardadas en: {raw.resolve()}")
        return 0
    except ApiFootballError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    finally:
        client.close()


if __name__ == "__main__":
    sys.exit(main())
