from __future__ import annotations

from app.config import Settings
from app.providers.api_football import ApiFootballProvider
from app.providers.base import DataProvider, ProviderError
from app.providers.csv_file import CsvProvider
from app.providers.demo import DemoProvider


def build_provider(settings: Settings) -> DataProvider:
    """Único lugar donde se elige la fuente de datos."""
    name = settings.data_provider.lower()
    if name == "demo":
        return DemoProvider()
    if name == "csv":
        return CsvProvider(settings.csv_matches_path, settings.csv_goals_path)
    if name == "api_football":
        from app.providers.api_football.provider import DEFAULT_LEAGUES
        return ApiFootballProvider(settings.api_football_cache_dir, settings.api_football_leagues or DEFAULT_LEAGUES)
    raise ProviderError(f"Proveedor desconocido: {settings.data_provider}")


__all__ = ["build_provider", "DataProvider"]
