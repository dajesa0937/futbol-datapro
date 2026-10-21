"""Validación retrospectiva "walk-forward" (sin fuga de información).

Para cada bloque de fechas se reajusta el modelo SOLO con partidos anteriores al bloque y se
predice el bloque. Se compara contra dos referencias simples:
  - frecuencias: probabilidades históricas de local/empate/visitante en el entrenamiento.
  - poisson_liga: Poisson independiente con la media de goles local/visitante de la liga
    (sin fuerza de equipos).
Métricas: Brier multiclase (menor es mejor; 0 = perfecto, 0.667 = predecir 1/3 siempre),
log loss, error absoluto en goles totales esperados, y tabla de calibración.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from typing import Sequence

import numpy as np

from app.engine import dixon_coles as dc
from app.engine.markets import summarize

EPS = 1e-12


def brier(probs: np.ndarray, outcomes: np.ndarray) -> float:
    onehot = np.eye(3)[outcomes]
    return float(np.mean(np.sum((probs - onehot) ** 2, axis=1)))


def log_loss(probs: np.ndarray, outcomes: np.ndarray) -> float:
    return float(-np.mean(np.log(np.clip(probs[np.arange(len(outcomes)), outcomes], EPS, 1))))


def calibration_table(probs: np.ndarray, outcomes: np.ndarray, bins: int = 10) -> list[dict]:
    """Agrupa todas las probabilidades (3 por partido) por intervalos y compara con la frecuencia real."""
    onehot = np.eye(3)[outcomes].ravel()
    p = probs.ravel()
    edges = np.linspace(0, 1, bins + 1)
    rows = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        mask = (p >= lo) & (p < hi if hi < 1 else p <= hi)
        n = int(mask.sum())
        rows.append({"bin": f"{lo:.1f}-{hi:.1f}", "n": n,
                     "mean_predicted": float(p[mask].mean()) if n else None,
                     "observed_freq": float(onehot[mask].mean()) if n else None})
    return rows


def outcome_index(hg: int, ag: int) -> int:
    return 0 if hg > ag else (1 if hg == ag else 2)  # 0 local, 1 empate, 2 visitante


def walk_forward(matches: Sequence, min_train: int = 150, step_days: int = 7,
                 min_team_matches: int = 8, xi: float = dc.DEFAULT_XI, ridge: float = dc.DEFAULT_RIDGE) -> dict:
    ordered = sorted(matches, key=lambda m: m.date)
    if len(ordered) <= min_train + 20:
        return {"status": "insufficient_data", "n_matches": len(ordered),
                "message": f"Se necesitan más de {min_train + 20} partidos para validar; hay {len(ordered)}."}

    start = ordered[min_train].date
    last = ordered[-1].date
    block_start = start
    pred_dc, pred_freq, pred_pois, outs = [], [], [], []
    xg_err_dc, xg_err_base = [], []
    by_season: dict[str, list[int]] = defaultdict(list)

    while block_start <= last:
        this_start = block_start
        block_end = this_start + timedelta(days=step_days)
        train = [m for m in ordered if m.date < this_start]
        test = [m for m in ordered if this_start <= m.date < block_end]
        block_start = block_end
        if not test or len(train) < 30:
            continue
        try:
            model = dc.fit(train, as_of=this_start, xi=xi, ridge=ridge)
        except dc.InsufficientDataError:
            continue
        hg_mean = np.mean([m.home_goals for m in train])
        ag_mean = np.mean([m.away_goals for m in train])
        freq = np.array([np.mean([m.home_goals > m.away_goals for m in train]),
                         np.mean([m.home_goals == m.away_goals for m in train]),
                         np.mean([m.home_goals < m.away_goals for m in train])])
        base_summary = summarize(dc.score_matrix(float(hg_mean), float(ag_mean), 0.0))
        base_probs = np.array([base_summary["p_home"], base_summary["p_draw"], base_summary["p_away"]])
        for m in test:
            if (model.matches_per_team.get(m.home, 0) < min_team_matches
                    or model.matches_per_team.get(m.away, 0) < min_team_matches):
                continue
            s = summarize(model.score_matrix(m.home, m.away))
            pred_dc.append([s["p_home"], s["p_draw"], s["p_away"]])
            pred_freq.append(freq)
            pred_pois.append(base_probs)
            o = outcome_index(m.home_goals, m.away_goals)
            outs.append(o)
            real_total = m.home_goals + m.away_goals
            xg_err_dc.append(abs(s["expected_home_goals"] + s["expected_away_goals"] - real_total))
            xg_err_base.append(abs(hg_mean + ag_mean - real_total))
            by_season[m.season].append(len(outs) - 1)

    if len(outs) < 30:
        return {"status": "insufficient_data", "n_matches": len(outs),
                "message": "Muy pocos partidos evaluables para validar."}

    P_dc, P_freq, P_pois, y = map(np.array, (pred_dc, pred_freq, pred_pois, outs))
    metrics = {
        "dixon_coles": {"brier": brier(P_dc, y), "log_loss": log_loss(P_dc, y), "mae_total_goals": float(np.mean(xg_err_dc))},
        "frecuencias": {"brier": brier(P_freq, y), "log_loss": log_loss(P_freq, y), "mae_total_goals": None},
        "poisson_liga": {"brier": brier(P_pois, y), "log_loss": log_loss(P_pois, y), "mae_total_goals": float(np.mean(xg_err_base))},
    }
    per_season = {}
    for season, idxs in by_season.items():
        if len(idxs) >= 20:
            per_season[season] = {"n": len(idxs), "brier_dc": brier(P_dc[idxs], y[idxs]),
                                  "brier_frecuencias": brier(P_freq[idxs], y[idxs])}
    # Mejora relativa del Brier frente a la mejor referencia
    best_base = min(metrics["frecuencias"]["brier"], metrics["poisson_liga"]["brier"])
    improvement = 1 - metrics["dixon_coles"]["brier"] / best_base
    return {
        "status": "ok", "n_evaluated": int(len(y)),
        "period": {"from": str(start), "to": str(last)},
        "method": f"walk-forward semanal; entrenamiento mínimo {min_train} partidos; xi={xi}; ridge={ridge}",
        "metrics": metrics,
        "brier_improvement_vs_best_baseline": float(improvement),
        "calibration": calibration_table(P_dc, y),
        "per_season": per_season,
        "outcome_rates": {"local": float(np.mean(y == 0)), "empate": float(np.mean(y == 1)), "visitante": float(np.mean(y == 2))},
    }
