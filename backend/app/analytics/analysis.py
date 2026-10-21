"""Orquesta un análisis completo de un partido: informe por equipo + predicción + calidad de datos."""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Sequence

import numpy as np

from app.analytics.team_report import INTERVAL_LABELS, last_matches, team_report
from app.engine import cards as cards_engine
from app.engine import dixon_coles as dc
from app.engine.markets import monte_carlo, summarize
from app.schemas import Competition, Match

MODEL_VERSION = "dc-1.0"
# Competiciones usadas para ajustar el modelo (fuerza ofensiva/defensiva). Los amistosos se
# excluyen por defecto: su intensidad y alineaciones no son comparables con partidos oficiales.
TRAIN_COMPETITIONS = {Competition.LIGA, Competition.COPA, Competition.INTERNACIONAL}


class AnalysisError(ValueError):
    pass


def sufficiency(n_home: int, n_away: int) -> dict:
    """Nivel de suficiencia de DATOS (no es una probabilidad de acierto)."""
    low = min(n_home, n_away)
    if low < 10:
        level, msg = "insuficiente", "Hay muy pocos partidos previos: la estimación NO es fiable."
    elif low < 20:
        level, msg = "baja", "Menos de 20 partidos previos de algún equipo: usar con mucha cautela."
    elif low < 40:
        level, msg = "media", "Muestra razonable de partidos previos."
    else:
        level, msg = "alta", "Muestra amplia de partidos previos."
    return {"level": level, "message": msg, "matches_home": n_home, "matches_away": n_away}


def _interval_expectation(report: dict, league_share: list[float], expected_goals: float) -> dict | None:
    """Reparte los goles esperados por tramo: mezcla la distribución del equipo con la de la liga."""
    g = report["goals_by_interval"]
    coverage = g["matches_with_data"] / g["of"] if g["of"] else 0
    if coverage < 0.6:
        return None
    team_counts = np.array(g["for"], dtype=float)
    prior = np.array(league_share) * 6.0  # 6 goles "virtuales" de la liga
    share = (team_counts + prior) / (team_counts.sum() + prior.sum())
    return {"labels": INTERVAL_LABELS, "expected": [float(expected_goals * s) for s in share]}


def league_interval_share(matches: Sequence[Match]) -> list[float]:
    counts = np.zeros(len(INTERVAL_LABELS))
    from app.analytics.team_report import _interval_index
    for m in matches:
        if m.goals:
            for g in m.goals:
                counts[_interval_index(g.minute)] += 1
    if counts.sum() == 0:
        return [1 / len(counts)] * len(counts)
    return list(counts / counts.sum())


def analyze_match(all_matches: Sequence[Match], home: str, away: str, on: date,
                  source_info: dict | None = None) -> dict:
    if home == away:
        raise AnalysisError("Elige dos equipos distintos.")
    teams = {m.home for m in all_matches} | {m.away for m in all_matches}
    for t in (home, away):
        if t not in teams:
            raise AnalysisError(f"Equipo sin datos: {t}")

    prior_matches = [m for m in all_matches if m.date < on]
    rep_home = team_report(all_matches, home, on)
    rep_away = team_report(all_matches, away, on)

    train = [m for m in prior_matches if m.competition in TRAIN_COMPETITIONS]
    suff = sufficiency(rep_home["sample_size"], rep_away["sample_size"])

    prediction: dict | None = None
    prediction_error: str | None = None
    model_info: dict | None = None
    try:
        model = dc.fit(train, as_of=on)
        n_home = model.matches_per_team.get(home, 0)
        n_away = model.matches_per_team.get(away, 0)
        suff = sufficiency(n_home, n_away) | {"scope": "partidos oficiales usados por el modelo"}
        if suff["level"] == "insuficiente":
            prediction_error = suff["message"]
        else:
            lh, la = model.rates(home, away)
            matrix = model.score_matrix(home, away)
            summary = summarize(matrix)
            prediction = {
                **summary,
                "lambda_home": lh, "lambda_away": la,
                "monte_carlo": monte_carlo(matrix),
                "factors": _factors(model, home, away),
            }
            league_share = league_interval_share(train)
            prediction["goals_by_interval_expected"] = {
                "home": _interval_expectation(rep_home, league_share, summary["expected_home_goals"]),
                "away": _interval_expectation(rep_away, league_share, summary["expected_away_goals"]),
            }
            prediction["scorer_probabilities"] = _scorer_probs(rep_home, summary["expected_home_goals"], home) + \
                _scorer_probs(rep_away, summary["expected_away_goals"], away)
        model_info = {"version": MODEL_VERSION, "type": "Dixon-Coles con decaimiento temporal",
                      "trained_on_matches": model.n_matches, "as_of": str(model.as_of),
                      "xi_per_day": model.xi, "home_advantage": model.home_adv, "rho": model.rho,
                      "converged": model.converged,
                      "training_competitions": sorted(c.value for c in TRAIN_COMPETITIONS)}
    except dc.InsufficientDataError as exc:
        prediction_error = str(exc)

    cards = _cards(all_matches, rep_home, rep_away, home, away, on)

    return {
        "match": {"home": home, "away": away, "date": on.isoformat()},
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "data_cutoff": (on.isoformat() + " (partidos anteriores a esta fecha)"),
        "source": source_info,
        "home": rep_home, "away": rep_away,
        "prediction": prediction,
        "prediction_unavailable_reason": prediction_error,
        "data_sufficiency": suff,
        "model": model_info,
        "cards_estimate": cards,
        "context": {
            "rest_days": {"home": rep_home["days_since_last_match"], "away": rep_away["days_since_last_match"]},
            "weather": {"available": False, "reason": "Sin proveedor meteorológico verificado para fecha y estadio."},
            "lineups": {"available": False, "reason": "La fuente actual no ofrece alineaciones ni lesiones."},
        },
        "disclaimer": ("Estimación estadística, no una certeza ni una garantía de resultado. "
                       "Las probabilidades dependen de la calidad y cobertura de los datos."),
    }


def _factors(model: dc.DixonColes, home: str, away: str) -> list[dict]:
    """Factores que respaldan la predicción, en lenguaje comprensible."""
    f = []
    f.append({"name": "Ventaja de localía",
              "value": float(np.exp(model.home_adv)),
              "text": f"El modelo estima que jugar de local multiplica los goles esperados por {np.exp(model.home_adv):.2f}."})
    for team, role in ((home, "local"), (away, "visitante")):
        a, d = model.attack[team], model.defense[team]
        f.append({"name": f"Ataque de {team}", "value": float(np.exp(a)),
                  "text": f"{team} marca {'más' if a > 0 else 'menos'} que el promedio de la liga (factor {np.exp(a):.2f})."})
        f.append({"name": f"Defensa de {team}", "value": float(np.exp(-d)),
                  "text": f"{team} recibe {'menos' if d > 0 else 'más'} goles que el promedio (factor {np.exp(-d):.2f}; menor es mejor)."})
    return f


def _scorer_probs(report: dict, team_expected_goals: float, team: str) -> list[dict]:
    """P(al menos un gol) = 1 - exp(-participación * goles esperados del equipo).

    Solo con detalle de goleadores en >= 8 goles del equipo; es una estimación simple que
    asume que el jugador participa. No sabe si está lesionado, suspendido o es titular.
    """
    total = report["team_goals_with_scorer_detail"]
    if total < 8:
        return []
    out = []
    for s in report["top_scorers"][:3]:
        share = s["goals"] / total
        out.append({"team": team, "player": s["player"], "position": s["position"],
                    "p_scores": float(1 - np.exp(-share * team_expected_goals)),
                    "based_on_goals": s["goals"], "team_goals_sample": total,
                    "caveat": "Suponiendo que juega. No se conocen alineaciones ni lesiones."})
    return out


def _cards(all_matches, rep_home, rep_away, home, away, on) -> dict:
    def team_cards(team):
        out = []
        for m in last_matches(all_matches, team, on):
            if m.has_cards:
                y, r = (m.home_yellow, m.home_red) if m.home == team else (m.away_yellow, m.away_red)
                out.append(float(y + (r or 0)))
        return out

    hc, ac = team_cards(home), team_cards(away)
    league = [float((m.home_yellow + (m.home_red or 0)) ) for m in all_matches if m.date < on and m.has_cards] + \
             [float((m.away_yellow + (m.away_red or 0))) for m in all_matches if m.date < on and m.has_cards]
    if not league:
        return {"reliable": False, "reason": "La fuente no ofrece tarjetas."}
    est = cards_engine.estimate(hc, ac, float(np.mean(league)))
    return {k: v for k, v in est.__dict__.items()} | {"kind": "estimación simple (sin validar)"}
