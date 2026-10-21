"""Mercados derivados de una matriz de marcadores, y simulación Monte Carlo."""
from __future__ import annotations

import numpy as np

OU_LINES = (0.5, 1.5, 2.5, 3.5, 4.5)


def summarize(m: np.ndarray, top: int = 8) -> dict:
    """Probabilidades exactas (analíticas) a partir de la matriz de marcadores."""
    n = m.shape[0]
    i, j = np.indices(m.shape)
    p_home = float(m[i > j].sum())
    p_draw = float(m[i == j].sum())
    p_away = float(m[i < j].sum())
    total = (i + j).ravel()
    flat = m.ravel()
    total_dist = np.bincount(total, weights=flat, minlength=2 * n - 1)
    cdf = np.cumsum(total_dist)
    lo = int(np.searchsorted(cdf, 0.10))
    hi = int(np.searchsorted(cdf, 0.90))
    order = np.argsort(flat)[::-1][:top]
    scores = [{"home": int(k // n), "away": int(k % n), "prob": float(flat[k])} for k in order]
    return {
        "p_home": p_home, "p_draw": p_draw, "p_away": p_away,
        "expected_home_goals": float((m.sum(axis=1) * np.arange(n)).sum()),
        "expected_away_goals": float((m.sum(axis=0) * np.arange(n)).sum()),
        "p_btts": float(m[1:, 1:].sum()),
        "over_under": {str(line): {"over": float(total_dist[int(line) + 1:].sum()),
                                   "under": float(total_dist[:int(line) + 1].sum())} for line in OU_LINES},
        "total_goals_range_80": [lo, hi],
        "top_scores": scores,
        "total_goals_distribution": [float(x) for x in total_dist[:9]],
    }


def monte_carlo(m: np.ndarray, n_sims: int = 20000, seed: int = 7) -> dict:
    """Simula `n_sims` partidos desde la matriz. Con semilla fija el resultado es reproducible.

    Devuelve frecuencias simuladas y su error estándar, útil para comprobar que la simulación
    concuerda con el cálculo analítico y para mostrar la incertidumbre numérica.
    """
    rng = np.random.default_rng(seed)
    n = m.shape[0]
    draws = rng.choice(m.size, size=n_sims, p=m.ravel())
    hg, ag = draws // n, draws % n

    def freq(mask):
        p = float(mask.mean())
        return {"prob": p, "std_error": float(np.sqrt(p * (1 - p) / n_sims))}

    return {
        "n_sims": n_sims, "seed": seed,
        "p_home": freq(hg > ag), "p_draw": freq(hg == ag), "p_away": freq(hg < ag),
        "p_btts": freq((hg > 0) & (ag > 0)),
        "over_2_5": freq(hg + ag > 2),
    }
