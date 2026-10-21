"""Caché local de respuestas CRUDAS. Estructura:

  <cache>/fixtures/<league>_<season>.json     respuesta de /fixtures
  <cache>/events/<fixture_id>.json            respuesta de /fixtures/events
  <cache>/statistics/<fixture_id>.json        respuesta de /fixtures/statistics
  <cache>/sync_state.json                     marcas de tiempo y contadores
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


class RawCache:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def _path(self, kind: str, name: str) -> Path:
        return self.root / kind / f"{name}.json"

    def has(self, kind: str, name: str) -> bool:
        return self._path(kind, name).exists()

    def read(self, kind: str, name: str) -> dict | None:
        p = self._path(kind, name)
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None

    def write(self, kind: str, name: str, body: dict) -> None:
        p = self._path(kind, name)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(body, ensure_ascii=False), encoding="utf-8")

    def fixture_files(self) -> list[Path]:
        d = self.root / "fixtures"
        return sorted(d.glob("*.json")) if d.exists() else []

    def read_state(self) -> dict:
        p = self.root / "sync_state.json"
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}

    def write_state(self, **updates) -> None:
        state = self.read_state() | updates
        state["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "sync_state.json").write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
