"""Modelos de dominio compartidos por proveedores, motor estadístico y API."""
from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


class Competition(str, Enum):
    LIGA = "liga_betplay"
    COPA = "copa_colombia"
    INTERNACIONAL = "internacional"
    AMISTOSO = "amistoso"


COMPETITION_LABELS = {
    Competition.LIGA: "Liga BetPlay",
    Competition.COPA: "Copa Colombia",
    Competition.INTERNACIONAL: "Torneo internacional",
    Competition.AMISTOSO: "Amistoso",
}


class GoalEvent(BaseModel):
    team: str
    minute: int = Field(ge=1, le=130)
    player: str | None = None
    position: str | None = None  # POR, DEF, MED, DEL


class Match(BaseModel):
    """Partido ya disputado. Los campos opcionales son None cuando el proveedor no los ofrece."""

    id: str
    date: date
    competition: Competition
    season: str
    home: str
    away: str
    home_goals: int = Field(ge=0, le=30)
    away_goals: int = Field(ge=0, le=30)
    home_yellow: int | None = Field(default=None, ge=0)
    away_yellow: int | None = Field(default=None, ge=0)
    home_red: int | None = Field(default=None, ge=0)
    away_red: int | None = Field(default=None, ge=0)
    referee: str | None = None
    venue: str | None = None
    goals: list[GoalEvent] | None = None  # None = el proveedor no tiene minuto a minuto

    @property
    def has_cards(self) -> bool:
        return self.home_yellow is not None and self.away_yellow is not None


class Fixture(BaseModel):
    id: str
    date: date
    kickoff: str | None = None  # "19:30" hora local, si se conoce
    competition: Competition
    season: str
    home: str
    away: str
    venue: str | None = None
    referee: str | None = None


class SourceInfo(BaseModel):
    name: str
    kind: str  # demo | csv | api
    is_demo: bool
    updated_at: datetime
    license_note: str
    coverage: dict[str, float | int | str | None]
    notes: list[str] = Field(default_factory=list)
    validation: dict | None = None
