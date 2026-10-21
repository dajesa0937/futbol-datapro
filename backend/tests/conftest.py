import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import Settings  # noqa: E402
from app.providers.demo import DemoProvider  # noqa: E402


@pytest.fixture(scope="session")
def demo():
    return DemoProvider()


@pytest.fixture
def settings(tmp_path):
    return Settings(database_url=f"sqlite:///{tmp_path / 'test.db'}", rate_limit_per_minute=1000,
                    write_rate_limit_per_minute=1000)
