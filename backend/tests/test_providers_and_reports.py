from datetime import date

import pandas as pd
import pytest

from app.analytics.analysis import analyze_match, sufficiency
from app.analytics.team_report import last_matches, team_report
from app.providers import build_provider
from app.providers.base import ProviderError, ProviderNotConfigured, team_key
from app.providers.csv_file import CsvProvider
from app.config import Settings


def test_demo_data_is_flagged_and_has_no_fake_coverage(demo):
    info = demo.info()
    assert info.is_demo and info.kind == "demo"
    assert info.coverage["clima"] is None and info.coverage["alineaciones"] is None


def test_last_matches_are_strictly_before_and_capped(demo):
    team = demo.teams()[0]
    cutoff = date(2026, 6, 1)
    sample = last_matches(demo.matches(), team, cutoff, 20)
    assert len(sample) == 20
    assert all(m.date < cutoff for m in sample)
    assert [m.date for m in sample] == sorted((m.date for m in sample), reverse=True)


def test_team_report_totals_are_consistent(demo):
    rep = team_report(demo.matches(), demo.teams()[3], date(2026, 10, 24))
    o = rep["overall"]
    assert o["wins"] + o["draws"] + o["losses"] == o["n"] == rep["sample_size"] == 20
    assert rep["home"]["n"] + rep["away"]["n"] == 20
    assert sum(rep["goals_by_interval"]["for"]) == rep["team_goals_with_scorer_detail"] == o["goals_for"]
    assert set(rep["by_competition"]) <= {"liga_betplay", "copa_colombia", "amistoso", "internacional"}


def test_report_without_data_says_so(demo):
    rep = team_report(demo.matches(), demo.teams()[0], date(2025, 1, 1))
    assert rep["sample_size"] == 0 and rep["overall"]["gf_avg"] is None and not rep["enough_data"]


def test_prediction_refused_without_history(demo):
    a = analyze_match(demo.matches(), demo.teams()[0], demo.teams()[1], date(2025, 8, 1))
    assert a["prediction"] is None and a["prediction_unavailable_reason"]


def test_full_analysis_shape(demo):
    f = demo.fixtures()[0]
    a = analyze_match(demo.matches(), f.home, f.away, f.date, {"name": "demo", "is_demo": True})
    p = a["prediction"]
    assert p["p_home"] + p["p_draw"] + p["p_away"] == pytest.approx(1.0)
    assert a["context"]["weather"]["available"] is False
    assert "garantía" in a["disclaimer"]
    assert a["data_sufficiency"]["level"] in {"baja", "media", "alta"}


def test_sufficiency_levels():
    assert sufficiency(5, 30)["level"] == "insuficiente"
    assert sufficiency(15, 30)["level"] == "baja"
    assert sufficiency(25, 30)["level"] == "media"
    assert sufficiency(60, 50)["level"] == "alta"


def test_api_football_without_cache_is_not_faked(tmp_path):
    with pytest.raises(ProviderNotConfigured):
        build_provider(Settings(data_provider="api_football", api_football_cache_dir=str(tmp_path / "vacia")))
    with pytest.raises(ProviderError):
        build_provider(Settings(data_provider="inexistente"))


def _csv(tmp_path, rows, name="p.csv"):
    path = tmp_path / name
    pd.DataFrame(rows).to_csv(path, index=False)
    return str(path)


BASE = dict(competition="Liga", season="2026-II", home_goals=1, away_goals=0)


def test_csv_provider_validates_and_reports(tmp_path):
    rows = [
        dict(BASE, date="2026-09-01", home="Atlético  Norte", away="Real Sur"),
        dict(BASE, date="2026-09-01", home="Atletico Norte", away="Real Sur"),  # duplicado
        dict(BASE, date="2026-09-08", home="Real Sur", away="Real Sur"),         # mismo equipo
        dict(BASE, date="2026-09-15", home="Real Sur", away="Atlético Norte", competition="Torneo X"),
        dict(competition="Liga", season="2026-II", date="2026-10-30", home="Real Sur",
             away="Atlético Norte", home_goals=None, away_goals=None),          # próximo partido
    ]
    prov = CsvProvider(_csv(tmp_path, rows), today=date(2026, 10, 20))
    assert len(prov.matches()) == 1 and len(prov.fixtures()) == 1
    v = prov.info().validation
    assert v["duplicados_descartados"] == 1 and len(v["errores"]) == 2
    assert prov.info().is_demo is False
    assert team_key("Atlético") == team_key("atletico")


def test_csv_missing_columns_rejected(tmp_path):
    with pytest.raises(ProviderError):
        CsvProvider(_csv(tmp_path, [dict(date="2026-01-01", home="A", away="B")]))
    with pytest.raises(ProviderError):
        CsvProvider(str(tmp_path / "no_existe.csv"))
