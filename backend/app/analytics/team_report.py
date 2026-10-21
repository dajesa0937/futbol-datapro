"""Estadísticas descriptivas de los últimos N partidos de un equipo (anteriores a una fecha).

Todo lo que no se pueda calcular con los datos disponibles se devuelve como None y con su
cobertura explícita; nunca se rellena con valores inventados.
"""
from __future__ import annotations

from collections import Counter
from datetime import date
from typing import Sequence

from app.schemas import COMPETITION_LABELS, Match

INTERVALS = [(1, 15), (16, 30), (31, 45), (46, 60), (61, 75), (76, 130)]
INTERVAL_LABELS = ["0-15", "16-30", "31-45", "46-60", "61-75", "76-90+"]


def last_matches(matches: Sequence[Match], team: str, before: date, n: int = 20) -> list[Match]:
    """Últimos `n` partidos del equipo con fecha ESTRICTAMENTE anterior a `before`, del más reciente al más antiguo."""
    own = [m for m in matches if m.date < before and team in (m.home, m.away)]
    own.sort(key=lambda m: (m.date, m.id), reverse=True)
    return own[:n]


def _interval_index(minute: int) -> int:
    for i, (lo, hi) in enumerate(INTERVALS):
        if lo <= minute <= hi:
            return i
    return len(INTERVALS) - 1


def _result(m: Match, team: str) -> str:
    gf, ga = (m.home_goals, m.away_goals) if m.home == team else (m.away_goals, m.home_goals)
    return "G" if gf > ga else ("E" if gf == ga else "P")


def match_row(m: Match, team: str) -> dict:
    is_home = m.home == team
    gf, ga = (m.home_goals, m.away_goals) if is_home else (m.away_goals, m.home_goals)
    yellow, red = ((m.home_yellow, m.home_red) if is_home else (m.away_yellow, m.away_red))
    return {
        "id": m.id, "date": m.date.isoformat(), "competition": m.competition.value,
        "competition_label": COMPETITION_LABELS[m.competition], "season": m.season,
        "venue_role": "local" if is_home else "visitante", "opponent": m.away if is_home else m.home,
        "goals_for": gf, "goals_against": ga, "result": _result(m, team),
        "yellow": yellow, "red": red, "referee": m.referee,
    }


def _split(rows: list[dict]) -> dict:
    n = len(rows)
    if n == 0:
        return {"n": 0, "wins": 0, "draws": 0, "losses": 0, "goals_for": 0, "goals_against": 0,
                "gf_avg": None, "ga_avg": None, "points_per_match": None}
    w = sum(r["result"] == "G" for r in rows)
    d = sum(r["result"] == "E" for r in rows)
    gf, ga = sum(r["goals_for"] for r in rows), sum(r["goals_against"] for r in rows)
    return {"n": n, "wins": w, "draws": d, "losses": n - w - d, "goals_for": gf, "goals_against": ga,
            "gf_avg": gf / n, "ga_avg": ga / n, "points_per_match": (3 * w + d) / n}


def team_report(matches: Sequence[Match], team: str, before: date, n: int = 20) -> dict:
    sample = last_matches(matches, team, before, n)
    rows = [match_row(m, team) for m in sample]
    overall = _split(rows)
    home_rows = [r for r in rows if r["venue_role"] == "local"]
    away_rows = [r for r in rows if r["venue_role"] == "visitante"]

    # Tarjetas
    with_cards = [r for r in rows if r["yellow"] is not None]
    cards = None
    if with_cards:
        cards = {
            "n": len(with_cards),
            "yellow_total": sum(r["yellow"] for r in with_cards),
            "red_total": sum(r["red"] or 0 for r in with_cards),
            "yellow_avg": sum(r["yellow"] for r in with_cards) / len(with_cards),
            "red_avg": sum(r["red"] or 0 for r in with_cards) / len(with_cards),
        }

    # Goles por intervalo de minutos (a favor y en contra) usando solo partidos con minuto a minuto
    with_events = [m for m in sample if m.goals is not None]
    interval_for = [0] * len(INTERVALS)
    interval_against = [0] * len(INTERVALS)
    scorers: Counter = Counter()
    scorer_pos: dict[str, str | None] = {}
    positions: Counter = Counter()
    events_goals_for = 0
    for m in with_events:
        for g in m.goals:
            idx = _interval_index(g.minute)
            if g.team == team:
                interval_for[idx] += 1
                events_goals_for += 1
                if g.player:
                    scorers[g.player] += 1
                    scorer_pos[g.player] = g.position
                if g.position:
                    positions[g.position] += 1
            else:
                interval_against[idx] += 1

    # Descanso: días desde el partido anterior al más reciente de la muestra y hasta `before`
    days_since_last = (before - sample[0].date).days if sample else None

    # Forma: puntos por partido en últimos 5 vs anteriores
    recent5 = rows[:5]
    prev = rows[5:]
    form = {
        "last5": "".join(r["result"] for r in recent5),
        "ppm_last5": _split(recent5)["points_per_match"],
        "ppm_previous": _split(prev)["points_per_match"],
    }

    by_comp: dict[str, dict] = {}
    for comp in sorted({r["competition"] for r in rows}):
        by_comp[comp] = _split([r for r in rows if r["competition"] == comp])
        by_comp[comp]["label"] = next(r["competition_label"] for r in rows if r["competition"] == comp)

    return {
        "team": team,
        "sample_size": len(rows),
        "requested": n,
        "enough_data": len(rows) >= n,
        "overall": overall,
        "home": _split(home_rows),
        "away": _split(away_rows),
        "form": form,
        "by_competition": by_comp,
        "cards": cards,
        "cards_coverage": {"matches_with_data": len(with_cards), "of": len(rows)},
        "goals_by_interval": {
            "labels": INTERVAL_LABELS, "for": interval_for, "against": interval_against,
            "matches_with_data": len(with_events), "of": len(rows),
        },
        "top_scorers": [{"player": p, "goals": g, "position": scorer_pos.get(p)} for p, g in scorers.most_common(5)],
        "goals_by_position": dict(positions),
        "team_goals_with_scorer_detail": events_goals_for,
        "days_since_last_match": days_since_last,
        "matches": rows,
    }
