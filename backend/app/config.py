"""Configuración leída de variables de entorno. Nunca se escriben credenciales en el código."""
from __future__ import annotations

import os
from dataclasses import dataclass, field


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "si", "sí"}


@dataclass(frozen=True)
class Settings:
    environment: str = "development"
    data_provider: str = "demo"  # demo | csv | api_football (pendiente)
    csv_matches_path: str = "data/partidos.csv"
    csv_goals_path: str | None = None
    database_url: str = "sqlite:///./datapro.db"
    cors_origins: tuple[str, ...] = ("http://localhost:3000",)
    rate_limit_per_minute: int = 120
    write_rate_limit_per_minute: int = 10
    trust_proxy: bool = False
    history_max_rows: int = 1000
    api_football_key: str | None = field(default=None, repr=False)  # nunca se imprime
    api_football_cache_dir: str = "data/cache/api_football"
    api_football_leagues: str | None = None  # "239:liga_betplay,241:copa_colombia" (ids por verificar)

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


def load_settings() -> Settings:
    origins = os.getenv("CORS_ORIGINS", "http://localhost:3000")
    return Settings(
        environment=os.getenv("APP_ENV", "development"),
        data_provider=os.getenv("DATA_PROVIDER", "demo"),
        csv_matches_path=os.getenv("CSV_MATCHES_PATH", "data/partidos.csv"),
        csv_goals_path=os.getenv("CSV_GOALS_PATH") or None,
        database_url=os.getenv("DATABASE_URL", "sqlite:///./datapro.db"),
        cors_origins=tuple(o.strip() for o in origins.split(",") if o.strip()),
        rate_limit_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "120")),
        write_rate_limit_per_minute=int(os.getenv("WRITE_RATE_LIMIT_PER_MINUTE", "10")),
        trust_proxy=_bool(os.getenv("TRUST_PROXY")),
        history_max_rows=int(os.getenv("HISTORY_MAX_ROWS", "1000")),
        api_football_key=os.getenv("API_FOOTBALL_KEY") or None,
        api_football_cache_dir=os.getenv("API_FOOTBALL_CACHE_DIR", "data/cache/api_football"),
        api_football_leagues=os.getenv("API_FOOTBALL_LEAGUES") or None,
    )
