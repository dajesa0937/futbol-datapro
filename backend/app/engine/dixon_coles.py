"""Modelo Dixon-Coles (1997) con decaimiento temporal y regularización.

lambda_local     = exp(mu + ventaja_local + ataque[local]    - defensa[visitante])
lambda_visitante = exp(mu + ataque[visitante] - defensa[local])

Los goles siguen una Poisson independiente, corregida por `tau(rho)` en los marcadores bajos
(0-0, 1-0, 0-1, 1-1), donde la independencia falla de forma conocida. Cada partido pesa
exp(-xi * días_transcurridos), de modo que el rendimiento reciente cuenta más.

Se añade una penalización ridge a ataque/defensa: con ~20 partidos por equipo, sin ella las
estimaciones extremas se sobreajustan. NO hay variables posteriores al partido: `fit` solo usa
partidos con fecha estrictamente anterior a `as_of`.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable, Protocol

import numpy as np
from scipy.optimize import minimize
from scipy.special import gammaln

MAX_GOALS = 10
DEFAULT_XI = 0.0019  # por día -> vida media ≈ 365 días
DEFAULT_RIDGE = 0.6


class MatchLike(Protocol):
    date: date
    home: str
    away: str
    home_goals: int
    away_goals: int


class InsufficientDataError(ValueError):
    pass


class UnknownTeamError(KeyError):
    pass


def _tau(hg, ag, lam, mu, rho):
    t = np.ones_like(lam)
    t = np.where((hg == 0) & (ag == 0), 1 - lam * mu * rho, t)
    t = np.where((hg == 0) & (ag == 1), 1 + lam * rho, t)
    t = np.where((hg == 1) & (ag == 0), 1 + mu * rho, t)
    t = np.where((hg == 1) & (ag == 1), 1 - rho, t)
    return t


@dataclass
class DixonColes:
    teams: list[str]
    mu: float
    home_adv: float
    rho: float
    attack: dict[str, float]
    defense: dict[str, float]
    n_matches: int
    matches_per_team: dict[str, int]
    effective_matches_per_team: dict[str, float]
    as_of: date
    xi: float
    converged: bool

    def rates(self, home: str, away: str) -> tuple[float, float]:
        for t in (home, away):
            if t not in self.attack:
                raise UnknownTeamError(t)
        lh = float(np.exp(self.mu + self.home_adv + self.attack[home] - self.defense[away]))
        la = float(np.exp(self.mu + self.attack[away] - self.defense[home]))
        return lh, la

    def score_matrix(self, home: str, away: str, max_goals: int = MAX_GOALS) -> np.ndarray:
        lh, la = self.rates(home, away)
        return score_matrix(lh, la, self.rho, max_goals)


def poisson_pmf(k: np.ndarray, lam: float) -> np.ndarray:
    return np.exp(k * np.log(lam) - lam - gammaln(k + 1))


def score_matrix(lh: float, la: float, rho: float = 0.0, max_goals: int = MAX_GOALS) -> np.ndarray:
    """Matriz P[i, j] = P(local i goles, visitante j goles), normalizada a 1."""
    k = np.arange(max_goals + 1)
    m = np.outer(poisson_pmf(k, lh), poisson_pmf(k, la))
    m[0, 0] *= max(1 - lh * la * rho, 1e-10)
    m[0, 1] *= max(1 + lh * rho, 1e-10)
    m[1, 0] *= max(1 + la * rho, 1e-10)
    m[1, 1] *= max(1 - rho, 1e-10)
    return m / m.sum()


def fit(matches: Iterable[MatchLike], as_of: date, xi: float = DEFAULT_XI,
        ridge: float = DEFAULT_RIDGE, min_matches: int = 30) -> DixonColes:
    """Ajusta el modelo con partidos ANTERIORES a `as_of`."""
    data = [m for m in matches if m.date < as_of]
    if len(data) < min_matches:
        raise InsufficientDataError(f"Solo {len(data)} partidos previos a {as_of}; mínimo {min_matches}.")

    teams = sorted({m.home for m in data} | {m.away for m in data})
    index = {t: i for i, t in enumerate(teams)}
    n = len(teams)
    hi = np.array([index[m.home] for m in data])
    ai = np.array([index[m.away] for m in data])
    hg = np.array([m.home_goals for m in data])
    ag = np.array([m.away_goals for m in data])
    days = np.array([(as_of - m.date).days for m in data], dtype=float)
    w = np.exp(-xi * days)

    def unpack(x):
        return x[0], x[1], x[2], x[3:3 + n], x[3 + n:]

    def nll(x):
        mu, h, rho, a, d = unpack(x)
        lam = np.exp(mu + h + a[hi] - d[ai])
        mu_a = np.exp(mu + a[ai] - d[hi])
        tau = np.maximum(_tau(hg, ag, lam, mu_a, rho), 1e-10)
        ll = w * (hg * np.log(lam) - lam + ag * np.log(mu_a) - mu_a + np.log(tau))
        return -ll.sum() + ridge * (np.sum(a ** 2) + np.sum(d ** 2))

    x0 = np.concatenate([[0.1, 0.2, -0.05], np.zeros(n), np.zeros(n)])
    bounds = [(-1, 1), (-0.5, 1.0), (-0.3, 0.3)] + [(-2, 2)] * (2 * n)
    res = minimize(nll, x0, method="L-BFGS-B", bounds=bounds)
    mu, h, rho, a, d = unpack(res.x)
    # Centrar ataque/defensa (identificabilidad): el nivel medio se traslada a mu.
    mu = mu + a.mean() - d.mean()
    a, d = a - a.mean(), d - d.mean()

    counts = np.bincount(np.concatenate([hi, ai]), minlength=n)
    eff = np.bincount(hi, weights=w, minlength=n) + np.bincount(ai, weights=w, minlength=n)
    return DixonColes(
        teams=teams, mu=float(mu), home_adv=float(h), rho=float(rho),
        attack={t: float(a[i]) for t, i in index.items()},
        defense={t: float(d[i]) for t, i in index.items()},
        n_matches=len(data), matches_per_team={t: int(counts[i]) for t, i in index.items()},
        effective_matches_per_team={t: float(eff[i]) for t, i in index.items()},
        as_of=as_of, xi=xi, converged=bool(res.success),
    )
