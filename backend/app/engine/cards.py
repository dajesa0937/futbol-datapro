"""Estimación simple de tarjetas con contracción hacia la media de la liga.

NO es un modelo validado: es un estimador de tasas con contracción empírica (equivale a un
Gamma-Poisson). Se muestra solo si hay suficientes partidos con datos de tarjetas, y la interfaz
lo etiqueta como "estimación simple". Si hay datos del árbitro suficientes se aplica su factor.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.engine.dixon_coles import poisson_pmf

MIN_TEAM_MATCHES = 8
MIN_REFEREE_MATCHES = 8
PRIOR_STRENGTH = 6.0  # "partidos virtuales" de la media de liga


@dataclass
class CardEstimate:
    reliable: bool
    reason: str | None
    home_expected: float | None = None
    away_expected: float | None = None
    total_expected: float | None = None
    over_under: dict | None = None
    referee_factor: float | None = None
    referee_matches: int = 0
    league_mean_per_team: float | None = None


def shrunk_rate(team_values: list[float], league_mean: float) -> float:
    n = len(team_values)
    return (np.sum(team_values) + PRIOR_STRENGTH * league_mean) / (n + PRIOR_STRENGTH)


def estimate(home_cards: list[float], away_cards: list[float], league_mean: float,
             referee_cards: list[float] | None = None, referee_name_known: bool = False) -> CardEstimate:
    """`home_cards`/`away_cards`: tarjetas (amarillas + rojas) que recibió cada equipo en sus
    partidos recientes. `referee_cards`: tarjetas totales (ambos equipos) en partidos del árbitro."""
    if len(home_cards) < MIN_TEAM_MATCHES or len(away_cards) < MIN_TEAM_MATCHES:
        return CardEstimate(False, f"Menos de {MIN_TEAM_MATCHES} partidos con datos de tarjetas por equipo.")
    home_rate = shrunk_rate(home_cards, league_mean)
    away_rate = shrunk_rate(away_cards, league_mean)

    ref_factor, ref_n = None, 0
    if referee_cards is not None and len(referee_cards) >= MIN_REFEREE_MATCHES:
        # promedio de tarjetas totales por partido con ese árbitro / promedio de liga por partido
        ref_n = len(referee_cards)
        ref_mean = (np.sum(referee_cards) + PRIOR_STRENGTH * 2 * league_mean) / (ref_n + PRIOR_STRENGTH)
        ref_factor = float(ref_mean / (2 * league_mean))
        home_rate *= ref_factor
        away_rate *= ref_factor

    total = float(home_rate + away_rate)
    # Suma de dos Poisson independientes = Poisson(total) (se ignora la sobredispersión real).
    k = np.arange(0, 15)
    pmf = poisson_pmf(k, total)
    lines = {}
    for line in (2.5, 3.5, 4.5, 5.5):
        under = float(pmf[: int(line) + 1].sum())
        lines[str(line)] = {"over": 1 - under, "under": under}
    return CardEstimate(True, None, float(home_rate), float(away_rate), total, lines,
                        ref_factor, ref_n, float(league_mean))
