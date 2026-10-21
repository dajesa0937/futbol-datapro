"""Proveedor DEMOSTRATIVO.

Genera datos SINTÉTICOS con clubes y jugadores FICTICIOS. No representa resultados reales de la
Liga BetPlay ni de ningún club. Existe para poder probar la interfaz, el motor y la validación
mientras no haya un proveedor real contratado. La API y la interfaz marcan siempre estos datos
como DEMO.

Los parámetros "verdaderos" (ataque/defensa) se conocen, lo que permite comprobar que el motor
los recupera. Eso valida el código, NO el rendimiento predictivo sobre fútbol real.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import numpy as np

from app.providers.base import DataProvider
from app.schemas import Competition, Fixture, GoalEvent, Match, SourceInfo

TEAM_NAMES = [
    "Aurora FC", "Cordillera", "Sabana Real", "Unión Cafetera", "Caribe Sporting",
    "Fortaleza Andina", "Orinoquia United", "Pacífico Atlético", "Guaviare Juniors", "Páramo FC",
    "Cóndores del Sur", "Jaguares del Magdalena", "Tayrona SC", "Quindío Verde", "Altiplano Club",
    "Llanero FC", "Amazonas Deportivo", "Nevado Atlético", "Río Grande FC", "Esmeralda SC",
]
FIRST = ["J.", "A.", "C.", "L.", "M.", "D.", "S.", "E.", "F.", "R.", "N.", "H."]
LAST = [
    "Valderrama", "Montoya", "Quintero", "Salgado", "Caicedo", "Bedoya", "Ospina", "Escobar",
    "Marín", "Posada", "Lozano", "Cárdenas", "Rentería", "Mosquera", "Arboleda", "Tamayo",
    "Giraldo", "Zapata", "Cuesta", "Londoño", "Palacios", "Rivas", "Naranjo", "Peña",
]
REFEREES = [f"Árbitro Demo {i}" for i in range(1, 13)]
# Probabilidad relativa de gol por tramo (más goles al final, patrón típico del fútbol)
INTERVAL_EDGES = [(1, 15), (16, 30), (31, 45), (46, 60), (61, 75), (76, 93)]
INTERVAL_WEIGHTS = np.array([0.14, 0.15, 0.17, 0.17, 0.17, 0.20])
REFERENCE_DATE = date(2026, 10, 19)  # los datos demo llegan hasta el día anterior


class DemoProvider(DataProvider):
    def __init__(self, seed: int = 2026) -> None:
        self._rng = np.random.default_rng(seed)
        n = len(TEAM_NAMES)
        self.true_attack = self._rng.normal(0.0, 0.28, n)
        self.true_defense = self._rng.normal(0.0, 0.22, n)
        self.true_mu = 0.12
        self.true_home = 0.27
        self._players = self._build_players()
        self._card_rate = self._rng.normal(0.0, 0.18, n)
        self._referee_rate = self._rng.normal(0.0, 0.15, len(REFEREES))
        self._matches: list[Match] = []
        self._fixtures: list[Fixture] = []
        self._build()

    # ------------------------------------------------------------------ API pública
    def info(self) -> SourceInfo:
        with_cards = sum(1 for m in self._matches if m.has_cards)
        with_goals = sum(1 for m in self._matches if m.goals is not None)
        total = len(self._matches)
        return SourceInfo(
            name="Datos demostrativos (sintéticos)",
            kind="demo",
            is_demo=True,
            updated_at=datetime.now(timezone.utc),
            license_note="Generados localmente. No provienen de ningún proveedor ni de la Liga.",
            coverage={
                "partidos": total,
                "equipos": len(TEAM_NAMES),
                "con_tarjetas_pct": round(100 * with_cards / total, 1),
                "con_minutos_de_gol_pct": round(100 * with_goals / total, 1),
                "clima": None,
                "alineaciones": None,
                "xg": None,
            },
            notes=[
                "Clubes, jugadores y árbitros son ficticios.",
                "No hay alineaciones, lesiones ni clima en esta fuente.",
                "Los resultados NO son reales: no usar para decisiones.",
            ],
        )

    def teams(self) -> list[str]:
        return list(TEAM_NAMES)

    def matches(self) -> list[Match]:
        return list(self._matches)

    def fixtures(self) -> list[Fixture]:
        return list(self._fixtures)

    # ------------------------------------------------------------------ generación
    def _build_players(self) -> dict[str, list[tuple[str, str, float]]]:
        players: dict[str, list[tuple[str, str, float]]] = {}
        positions = ["DEL"] * 4 + ["MED"] * 5 + ["DEF"] * 5
        weights_by_pos = {"DEL": 3.0, "MED": 1.4, "DEF": 0.5}
        for t in TEAM_NAMES:
            names: set[str] = set()
            roster = []
            for pos in positions:
                while True:
                    nm = f"{self._rng.choice(FIRST)} {self._rng.choice(LAST)}"
                    if nm not in names:
                        names.add(nm)
                        break
                w = weights_by_pos[pos] * float(self._rng.uniform(0.5, 1.5))
                roster.append((nm, pos, w))
            players[t] = roster
        return players

    def _lambdas(self, h: int, a: int) -> tuple[float, float]:
        lh = np.exp(self.true_mu + self.true_home + self.true_attack[h] - self.true_defense[a])
        la = np.exp(self.true_mu + self.true_attack[a] - self.true_defense[h])
        return float(lh), float(la)

    def _goal_events(self, team: str, n_goals: int) -> list[GoalEvent]:
        roster = self._players[team]
        w = np.array([p[2] for p in roster])
        w = w / w.sum()
        events = []
        for _ in range(n_goals):
            idx = int(self._rng.choice(len(roster), p=w))
            interval = int(self._rng.choice(len(INTERVAL_EDGES), p=INTERVAL_WEIGHTS))
            lo, hi = INTERVAL_EDGES[interval]
            events.append(
                GoalEvent(team=team, minute=int(self._rng.integers(lo, hi + 1)),
                          player=roster[idx][0], position=roster[idx][1])
            )
        return sorted(events, key=lambda e: e.minute)

    def _play(self, mid: str, day: date, comp: Competition, season: str, h: int, a: int) -> Match:
        lh, la = self._lambdas(h, a)
        hg, ag = int(self._rng.poisson(lh)), int(self._rng.poisson(la))
        ref_idx = int(self._rng.integers(0, len(REFEREES)))
        base = 2.0
        hy = int(self._rng.poisson(base * np.exp(self._card_rate[h] + self._referee_rate[ref_idx])))
        ay = int(self._rng.poisson(base * np.exp(self._card_rate[a] + self._referee_rate[ref_idx])))
        hr, ar = int(self._rng.random() < 0.07), int(self._rng.random() < 0.07)
        th, ta = TEAM_NAMES[h], TEAM_NAMES[a]
        return Match(
            id=mid, date=day, competition=comp, season=season, home=th, away=ta,
            home_goals=hg, away_goals=ag, home_yellow=hy, away_yellow=ay,
            home_red=hr, away_red=ar, referee=REFEREES[ref_idx], venue=f"Estadio de {th}",
            goals=self._goal_events(th, hg) + self._goal_events(ta, ag),
        )

    def _round_robin(self, start: date, n_rounds: int, flip: bool) -> list[list[tuple[int, int]]]:
        n = len(TEAM_NAMES)
        idx = list(range(n))
        rounds = []
        for r in range(n - 1):
            pairs = []
            for i in range(n // 2):
                x, y = idx[i], idx[n - 1 - i]
                pairs.append((y, x) if (r + i) % 2 else (x, y))
            if flip:
                pairs = [(b, a) for a, b in pairs]
            rounds.append(pairs)
            idx = [idx[0]] + [idx[-1]] + idx[1:-1]
        return rounds[:n_rounds]

    def _build(self) -> None:
        counter = 0
        # Tres torneos de liga: 2025-II completo, 2026-I completo y 2026-II (8 fechas jugadas).
        tournaments = [
            ("2025-II", date(2025, 7, 19), 19), ("2026-I", date(2026, 1, 24), 19),
            ("2026-II", date(2026, 8, 22), 8),
        ]
        liga_days: list[date] = []
        for season, start, played in tournaments:
            rounds = self._round_robin(start, played, flip=False)
            for r, pairs in enumerate(rounds):
                day = start + timedelta(days=7 * r)
                liga_days.append(day)
                for h, a in pairs:
                    counter += 1
                    self._matches.append(self._play(f"demo-{counter:04d}", day, Competition.LIGA, season, h, a))
        # Copa Colombia y amistosos intercalados.
        for k in range(60):
            h, a = (int(x) for x in self._rng.choice(len(TEAM_NAMES), 2, replace=False))
            day = date(2025, 8, 1) + timedelta(days=int(self._rng.integers(0, 440)) + 3)
            if day >= REFERENCE_DATE:
                continue
            counter += 1
            self._matches.append(self._play(f"demo-{counter:04d}", day, Competition.COPA, "Copa 2025-26", h, a))
        for k in range(40):
            h, a = (int(x) for x in self._rng.choice(len(TEAM_NAMES), 2, replace=False))
            day = date(2026, 1, 3) + timedelta(days=int(self._rng.integers(0, 15)))
            counter += 1
            self._matches.append(self._play(f"demo-{counter:04d}", day, Competition.AMISTOSO, "Pretemporada 2026", h, a))
        self._matches = [m for m in self._matches if m.date < REFERENCE_DATE]
        self._matches.sort(key=lambda m: (m.date, m.id))

        # Próxima fecha de liga (fecha 9 del 2026-II): partidos programados, sin resultado.
        next_round = self._round_robin(date(2026, 8, 22), 9, flip=False)[8]
        kickoff_day = date(2026, 10, 24)
        times = ["15:30", "17:45", "20:00", "18:00", "19:30"]
        for i, (h, a) in enumerate(next_round):
            self._fixtures.append(
                Fixture(id=f"demo-fx-{i + 1:02d}", date=kickoff_day + timedelta(days=i % 2),
                        kickoff=times[i % len(times)], competition=Competition.LIGA,
                        season="2026-II", home=TEAM_NAMES[h], away=TEAM_NAMES[a],
                        venue=f"Estadio de {TEAM_NAMES[h]}")
            )
