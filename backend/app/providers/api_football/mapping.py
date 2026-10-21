"""Conversión de respuestas crudas de API-Football a los modelos de dominio.

Funciones puras (sin red) para poder probarlas con respuestas guardadas.
Supuestos NO verificados con respuestas reales (confirmar con `scripts/api_football_cobertura.py`):
  - fixture.date es ISO-8601 con zona horaria; se convierte a fecha local de Bogotá.
  - Estados finalizados: FT, AET, PEN. Próximos: NS, TBD. Cualquier otro se ignora.
  - Eventos de gol: type == "Goal" con detail "Normal Goal" | "Penalty" | "Own Goal".
    El equipo atribuido a un autogol puede variar: por eso se valida que el conteo por equipo
    coincida con el marcador y, si no coincide, el detalle de goles se descarta (queda None)
    y el partido se anota en el informe de calidad.
  - Estadísticas: type "Yellow Cards" / "Red Cards"; un valor null con estadísticas presentes
    se interpreta como 0.
"""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from app.providers.base import normalize_team_name
from app.schemas import Competition, Fixture, GoalEvent, Match

TZ = ZoneInfo("America/Bogota")
FINISHED = {"FT", "AET", "PEN"}
UPCOMING = {"NS", "TBD"}


def local_date_and_time(iso: str):
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(TZ)
    return dt.date(), dt.strftime("%H:%M")


def season_label(item: dict) -> str:
    """'2025 Apertura' si la ronda trae etapa ('Apertura - 5'); si no, solo el año."""
    year = item.get("league", {}).get("season")
    rnd = item.get("league", {}).get("round") or ""
    stage = rnd.split(" - ")[0].strip() if " - " in rnd else ""
    return f"{year} {stage}".strip() if stage else str(year)


def status_of(item: dict) -> str:
    return (item.get("fixture", {}).get("status", {}) or {}).get("short", "")


def map_finished(item: dict, competition: Competition) -> Match | None:
    if status_of(item) not in FINISHED:
        return None
    goals = item.get("goals", {})
    if goals.get("home") is None or goals.get("away") is None:
        return None
    day, _ = local_date_and_time(item["fixture"]["date"])
    fx = item["fixture"]
    return Match(
        id=f"apif-{fx['id']}", date=day, competition=competition, season=season_label(item),
        home=normalize_team_name(item["teams"]["home"]["name"]),
        away=normalize_team_name(item["teams"]["away"]["name"]),
        home_goals=int(goals["home"]), away_goals=int(goals["away"]),
        referee=(fx.get("referee") or None), venue=((fx.get("venue") or {}).get("name") or None),
    )


def map_upcoming(item: dict, competition: Competition) -> Fixture | None:
    if status_of(item) not in UPCOMING:
        return None
    fx = item["fixture"]
    day, hhmm = local_date_and_time(fx["date"])
    return Fixture(
        id=f"apif-{fx['id']}", date=day, kickoff=hhmm if status_of(item) == "NS" else None,
        competition=competition, season=season_label(item),
        home=normalize_team_name(item["teams"]["home"]["name"]),
        away=normalize_team_name(item["teams"]["away"]["name"]),
        venue=((fx.get("venue") or {}).get("name") or None), referee=(fx.get("referee") or None),
    )


def apply_events(match: Match, events: list[dict]) -> tuple[Match, str | None]:
    """Añade el detalle de goles si es coherente con el marcador. Devuelve (partido, problema|None)."""
    goals: list[GoalEvent] = []
    for e in events:
        if e.get("type") != "Goal" or (e.get("detail") or "") in {"Missed Penalty"}:
            continue
        minute = (e.get("time") or {}).get("elapsed")
        team = normalize_team_name((e.get("team") or {}).get("name", ""))
        if minute is None or not team:
            continue
        goals.append(GoalEvent(team=team, minute=max(1, min(int(minute), 130)),
                               player=((e.get("player") or {}).get("name") or None), position=None))
    home_n = sum(g.team == match.home for g in goals)
    away_n = sum(g.team == match.away for g in goals)
    if (home_n, away_n) != (match.home_goals, match.away_goals):
        return match, f"goles por evento {home_n}-{away_n} no coinciden con marcador {match.home_goals}-{match.away_goals}"
    return match.model_copy(update={"goals": sorted(goals, key=lambda g: g.minute)}), None


def apply_statistics(match: Match, stats: list[dict]) -> tuple[Match, str | None]:
    """`stats` es la lista de la respuesta de /fixtures/statistics: un elemento por equipo."""
    by_team: dict[str, dict[str, int]] = {}
    for block in stats:
        name = normalize_team_name((block.get("team") or {}).get("name", ""))
        vals = {s.get("type"): s.get("value") for s in block.get("statistics", [])}
        by_team[name] = {
            "yellow": int(vals.get("Yellow Cards") or 0),
            "red": int(vals.get("Red Cards") or 0),
            "has": int("Yellow Cards" in vals or "Red Cards" in vals),
        }
    h, a = by_team.get(match.home), by_team.get(match.away)
    if not h or not a or not (h["has"] and a["has"]):
        return match, "estadísticas de tarjetas ausentes para algún equipo"
    return match.model_copy(update={"home_yellow": h["yellow"], "home_red": h["red"],
                                    "away_yellow": a["yellow"], "away_red": a["red"]}), None
