from datetime import date

import numpy as np
import pytest

from app.engine import dixon_coles as dc
from app.engine import validation
from app.engine.markets import monte_carlo, summarize
from app.providers.demo import TEAM_NAMES

OFFICIAL = lambda ms: [m for m in ms if m.competition.value != "amistoso"]  # noqa: E731


def test_score_matrix_is_probability_distribution():
    m = dc.score_matrix(1.4, 1.1, rho=-0.08)
    assert m.sum() == pytest.approx(1.0)
    assert (m >= 0).all()


def test_summary_is_coherent():
    s = summarize(dc.score_matrix(1.6, 0.9, rho=-0.05))
    assert s["p_home"] + s["p_draw"] + s["p_away"] == pytest.approx(1.0)
    assert s["p_home"] > s["p_away"]
    assert s["over_under"]["2.5"]["over"] + s["over_under"]["2.5"]["under"] == pytest.approx(1.0)
    assert 0 < s["p_btts"] < 1
    assert s["top_scores"][0]["prob"] >= s["top_scores"][-1]["prob"]


def test_monte_carlo_agrees_with_analytic_within_error():
    m = dc.score_matrix(1.5, 1.2, rho=-0.06)
    exact, sim = summarize(m), monte_carlo(m, n_sims=40000, seed=1)
    for key, exact_key in (("p_home", "p_home"), ("p_draw", "p_draw"), ("p_away", "p_away"), ("p_btts", "p_btts")):
        assert abs(sim[key]["prob"] - exact[exact_key]) < 4 * sim[key]["std_error"] + 1e-9
    assert monte_carlo(m, 1000, seed=3) == monte_carlo(m, 1000, seed=3)  # reproducible


def test_fit_needs_enough_matches(demo):
    with pytest.raises(dc.InsufficientDataError):
        dc.fit(demo.matches()[:10], as_of=date(2027, 1, 1))


def test_fit_recovers_team_strengths(demo):
    model = dc.fit(OFFICIAL(demo.matches()), as_of=date(2026, 10, 24))
    est = np.array([model.attack[t] for t in TEAM_NAMES])
    true = demo.true_attack - demo.true_attack.mean()
    assert np.corrcoef(est, true)[0, 1] > 0.6
    assert model.home_adv > 0  # la ventaja de local sintética es positiva


def test_no_information_leak_in_fit(demo):
    """Resultados posteriores a `as_of` no pueden cambiar el modelo."""
    ms = OFFICIAL(demo.matches())
    cutoff = date(2026, 9, 1)
    base = dc.fit(ms, as_of=cutoff)
    tampered = [m.model_copy(update={"home_goals": 9, "away_goals": 0}) if m.date >= cutoff else m for m in ms]
    again = dc.fit(tampered, as_of=cutoff)
    assert base.attack == again.attack and base.mu == again.mu


def test_metrics_known_values():
    probs = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    assert validation.brier(probs, np.array([0, 1])) == pytest.approx(0.0)
    uniform = np.full((2, 3), 1 / 3)
    assert validation.brier(uniform, np.array([0, 1])) == pytest.approx(2 / 3)
    assert validation.log_loss(uniform, np.array([0, 1])) == pytest.approx(np.log(3))


def test_walk_forward_runs_and_reports(demo):
    res = validation.walk_forward(OFFICIAL(demo.matches()))
    assert res["status"] == "ok"
    assert res["n_evaluated"] > 100
    for name in ("dixon_coles", "frecuencias", "poisson_liga"):
        assert 0 < res["metrics"][name]["brier"] < 1
    assert sum(r["n"] for r in res["calibration"]) == res["n_evaluated"] * 3


def test_walk_forward_refuses_tiny_samples(demo):
    assert validation.walk_forward(demo.matches()[:50])["status"] == "insufficient_data"
