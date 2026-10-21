"""Contrato que debe cumplir cualquier proveedor de datos.

Cambiar de proveedor (demo -> CSV -> API de pago) no debe tocar el motor ni la API:
solo se registra otro proveedor en `providers/__init__.py`.
"""
from __future__ import annotations

import re
import unicodedata
from abc import ABC, abstractmethod

from app.schemas import Fixture, Match, SourceInfo


class ProviderError(RuntimeError):
    """Error genérico de un proveedor (datos inválidos, no configurado, etc.)."""


class ProviderNotConfigured(ProviderError):
    """El proveedor existe pero faltan credenciales o implementación."""


class DataProvider(ABC):
    @abstractmethod
    def info(self) -> SourceInfo: ...

    @abstractmethod
    def teams(self) -> list[str]: ...

    @abstractmethod
    def matches(self) -> list[Match]:
        """Todos los partidos terminados, sin ordenar."""

    @abstractmethod
    def fixtures(self) -> list[Fixture]:
        """Próximos partidos programados."""


def normalize_team_name(name: str) -> str:
    """Limpia espacios; la comparación usa `team_key` (sin tildes ni mayúsculas)."""
    return re.sub(r"\s+", " ", name).strip()


def team_key(name: str) -> str:
    decomposed = unicodedata.normalize("NFKD", name)
    ascii_only = "".join(c for c in decomposed if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", ascii_only.lower()).strip()
