"""Importación manual desde CSV o Excel (.xlsx) para pruebas y carga propia.

Columnas obligatorias de partidos: date, competition, season, home, away, home_goals, away_goals
Opcionales: id, home_yellow, away_yellow, home_red, away_red, referee, venue, kickoff
Filas sin home_goals/away_goals y con fecha futura se tratan como PRÓXIMOS partidos.

Archivo opcional de goles (minuto a minuto): match_id, team, minute, player, position.
Cada anomalía se registra en el informe de validación; nada se corrige en silencio.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

from app.providers.base import DataProvider, ProviderError, normalize_team_name, team_key
from app.schemas import Competition, Fixture, GoalEvent, Match, SourceInfo

REQUIRED = ["date", "competition", "season", "home", "away", "home_goals", "away_goals"]
COMPETITION_ALIASES = {
    "liga": Competition.LIGA, "liga betplay": Competition.LIGA, "liga_betplay": Competition.LIGA,
    "primera a": Competition.LIGA, "copa": Competition.COPA, "copa colombia": Competition.COPA,
    "copa_colombia": Competition.COPA, "internacional": Competition.INTERNACIONAL,
    "libertadores": Competition.INTERNACIONAL, "sudamericana": Competition.INTERNACIONAL,
    "amistoso": Competition.AMISTOSO,
}


def _read(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise ProviderError(f"No existe el archivo: {path}")
    if path.suffix.lower() in {".xlsx", ".xlsm"}:
        return pd.read_excel(path)
    return pd.read_csv(path)


def _opt_int(value) -> int | None:
    return None if pd.isna(value) else int(value)


def _opt_str(value) -> str | None:
    return None if pd.isna(value) else str(value).strip() or None


class CsvProvider(DataProvider):
    def __init__(self, matches_path: str, goals_path: str | None = None, today: date | None = None) -> None:
        self._today = today or date.today()
        self._report: dict = {"filas_leidas": 0, "errores": [], "duplicados_descartados": 0, "alias_unificados": {}}
        self._matches: list[Match] = []
        self._fixtures: list[Fixture] = []
        self._source = Path(matches_path)
        self._load(Path(matches_path), Path(goals_path) if goals_path else None)

    # ------------------------------------------------------------------ carga y validación
    def _load(self, matches_path: Path, goals_path: Path | None) -> None:
        df = _read(matches_path)
        missing = [c for c in REQUIRED if c not in df.columns]
        if missing:
            raise ProviderError(f"Faltan columnas obligatorias: {', '.join(missing)}")
        self._report["filas_leidas"] = len(df)

        canonical: dict[str, str] = {}  # team_key -> nombre canónico (primera forma vista)
        goals_by_match = self._load_goals(goals_path) if goals_path else None
        seen: set[tuple] = set()

        for i, row in df.iterrows():
            line = i + 2  # fila del archivo, contando el encabezado
            try:
                comp_raw = str(row["competition"]).strip().lower()
                comp = COMPETITION_ALIASES.get(comp_raw)
                if comp is None:
                    raise ValueError(f"competición desconocida '{row['competition']}'")
                day = pd.to_datetime(row["date"]).date()
                names = []
                for col in ("home", "away"):
                    raw = normalize_team_name(str(row[col]))
                    key = team_key(raw)
                    if key in canonical and canonical[key] != raw:
                        self._report["alias_unificados"][raw] = canonical[key]
                    canonical.setdefault(key, raw)
                    names.append(canonical[key])
                home, away = names
                if home == away:
                    raise ValueError("local y visitante son el mismo equipo")
                played = not (pd.isna(row["home_goals"]) or pd.isna(row["away_goals"]))
                mid = _opt_str(row.get("id")) or f"csv-{line}"
                if not played:
                    if day < self._today:
                        raise ValueError("partido pasado sin resultado")
                    self._fixtures.append(Fixture(
                        id=mid, date=day, kickoff=_opt_str(row.get("kickoff")), competition=comp,
                        season=str(row["season"]).strip(), home=home, away=away,
                        venue=_opt_str(row.get("venue")), referee=_opt_str(row.get("referee"))))
                    continue
                if day > self._today:
                    raise ValueError("partido con resultado y fecha futura")
                dedup_key = (day, team_key(home), team_key(away), comp)
                if dedup_key in seen:
                    self._report["duplicados_descartados"] += 1
                    continue
                seen.add(dedup_key)
                goals = None
                if goals_by_match is not None and mid in goals_by_match:
                    goals = goals_by_match[mid]
                    if len(goals) != int(row["home_goals"]) + int(row["away_goals"]):
                        raise ValueError("la suma de goles no coincide con el detalle de goles")
                self._matches.append(Match(
                    id=mid, date=day, competition=comp, season=str(row["season"]).strip(),
                    home=home, away=away, home_goals=int(row["home_goals"]), away_goals=int(row["away_goals"]),
                    home_yellow=_opt_int(row.get("home_yellow")), away_yellow=_opt_int(row.get("away_yellow")),
                    home_red=_opt_int(row.get("home_red")), away_red=_opt_int(row.get("away_red")),
                    referee=_opt_str(row.get("referee")), venue=_opt_str(row.get("venue")), goals=goals))
            except Exception as exc:  # una fila mala no tumba la carga; queda registrada
                self._report["errores"].append({"fila": line, "motivo": str(exc)})

        self._teams = sorted(canonical.values())

    def _load_goals(self, path: Path) -> dict[str, list[GoalEvent]]:
        gdf = _read(path)
        out: dict[str, list[GoalEvent]] = {}
        for _, r in gdf.iterrows():
            out.setdefault(str(r["match_id"]).strip(), []).append(
                GoalEvent(team=normalize_team_name(str(r["team"])), minute=int(r["minute"]),
                          player=_opt_str(r.get("player")), position=_opt_str(r.get("position"))))
        return out

    # ------------------------------------------------------------------ contrato
    def info(self) -> SourceInfo:
        total = len(self._matches)
        pct = lambda n: round(100 * n / total, 1) if total else 0.0  # noqa: E731
        return SourceInfo(
            name=f"Importación manual ({self._source.name})", kind="csv", is_demo=False,
            updated_at=datetime.fromtimestamp(self._source.stat().st_mtime, tz=timezone.utc),
            license_note="Datos cargados por el usuario; su licencia depende de la fuente original.",
            coverage={
                "partidos": total, "equipos": len(self._teams),
                "con_tarjetas_pct": pct(sum(1 for m in self._matches if m.has_cards)),
                "con_minutos_de_gol_pct": pct(sum(1 for m in self._matches if m.goals is not None)),
                "clima": None, "alineaciones": None, "xg": None,
            },
            notes=[f"{len(self._report['errores'])} filas rechazadas, "
                   f"{self._report['duplicados_descartados']} duplicados descartados."],
            validation=self._report,
        )

    def teams(self) -> list[str]:
        return list(self._teams)

    def matches(self) -> list[Match]:
        return list(self._matches)

    def fixtures(self) -> list[Fixture]:
        return list(self._fixtures)
