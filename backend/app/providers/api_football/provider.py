"""Proveedor que lee la caché local de API-Football (sin red).

Se llena con `python -m scripts.api_football_sync`. Cada partido sin detalle (minutos de gol,
tarjetas) sigue siendo válido para el modelo: solo se pierden esas secciones del dashboard,
y la cobertura real se informa en `info().coverage`.
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.providers.api_football.cache import RawCache
from app.providers.api_football import mapping
from app.providers.base import DataProvider, ProviderNotConfigured
from app.schemas import Competition, Fixture, Match, SourceInfo

DEFAULT_LEAGUES = "239:liga_betplay,241:copa_colombia"  # ids por VERIFICAR con el script de cobertura


def parse_leagues(spec: str) -> dict[int, Competition]:
    out: dict[int, Competition] = {}
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        lid, _, comp = part.partition(":")
        out[int(lid)] = Competition(comp)
    return out


class ApiFootballProvider(DataProvider):
    def __init__(self, cache_dir: str, leagues: str = DEFAULT_LEAGUES) -> None:
        self.cache = RawCache(cache_dir)
        self.leagues = parse_leagues(leagues)
        self._matches: dict[str, Match] = {}
        self._fixtures: list[Fixture] = []
        self.issues: list[dict] = []
        self._load()

    def _load(self) -> None:
        files = self.cache.fixture_files()
        if not files:
            raise ProviderNotConfigured(
                "No hay datos en la caché de API-Football. Ejecuta primero: "
                "python -m scripts.api_football_cobertura  y  python -m scripts.api_football_sync")
        for f in files:
            league_id = int(f.stem.split("_")[0])
            comp = self.leagues.get(league_id)
            if comp is None:
                continue  # liga en caché que no está configurada
            body = self.cache.read("fixtures", f.stem) or {}
            for item in body.get("response", []):
                m = mapping.map_finished(item, comp)
                if m is not None:
                    fid = item["fixture"]["id"]
                    ev = self.cache.read("events", str(fid))
                    if ev is not None:
                        m, problem = mapping.apply_events(m, ev.get("response", []))
                        if problem:
                            self.issues.append({"partido": m.id, "tipo": "goles", "detalle": problem})
                    st = self.cache.read("statistics", str(fid))
                    if st is not None:
                        m, problem = mapping.apply_statistics(m, st.get("response", []))
                        if problem:
                            self.issues.append({"partido": m.id, "tipo": "tarjetas", "detalle": problem})
                    self._matches[m.id] = m
                    continue
                fx = mapping.map_upcoming(item, comp)
                if fx is not None:
                    self._fixtures.append(fx)

    # ---------------------------------------------------------------- contrato
    def info(self) -> SourceInfo:
        total = len(self._matches)
        pct = lambda n: round(100 * n / total, 1) if total else 0.0  # noqa: E731
        state = self.cache.read_state()
        updated = state.get("updated_at")
        return SourceInfo(
            name="API-Football (caché local)", kind="api", is_demo=False,
            updated_at=datetime.fromisoformat(updated) if updated else datetime.now(timezone.utc),
            license_note="Datos de API-Football (api-sports.io). Verifica que tu plan permita su uso en un producto comercial.",
            coverage={
                "partidos": total, "equipos": len(self.teams()),
                "con_tarjetas_pct": pct(sum(1 for m in self._matches.values() if m.has_cards)),
                "con_minutos_de_gol_pct": pct(sum(1 for m in self._matches.values() if m.goals is not None)),
                "clima": None, "alineaciones": None, "xg": None,
                "ligas": ", ".join(f"{k}={v.value}" for k, v in self.leagues.items()),
            },
            notes=[f"{len(self.issues)} detalles descartados por incoherencia con el marcador o datos ausentes.",
                   "Posición de los goleadores no disponible (requiere alineaciones)."],
            validation={"incidencias": self.issues[:200], "sync": state},
        )

    def teams(self) -> list[str]:
        names = {m.home for m in self._matches.values()} | {m.away for m in self._matches.values()}
        names |= {f.home for f in self._fixtures} | {f.away for f in self._fixtures}
        return sorted(names)

    def matches(self) -> list[Match]:
        return list(self._matches.values())

    def fixtures(self) -> list[Fixture]:
        return list(self._fixtures)
