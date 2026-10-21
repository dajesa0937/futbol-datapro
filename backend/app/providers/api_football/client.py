"""Cliente HTTP de API-Football (api-sports.io) con presupuesto de consultas.

SOLO lo usan los scripts de sincronización (`scripts/api_football_*.py`). La aplicación web
nunca llama a la API: lee la caché local. Así una caída o el límite diario del proveedor no
tumban la interfaz, y cada consulta gastada queda guardada para siempre (se puede volver a
mapear sin gastar más).

ESTADO: escrito según el formato documentado (cabecera `x-apisports-key`, envoltorio
`get/parameters/errors/results/paging/response`). NO se ha ejecutado contra la API real desde
este entorno; el script de cobertura guarda respuestas crudas para ajustar el mapeo.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import httpx

BASE_URL = "https://v3.football.api-sports.io"


class ApiFootballError(RuntimeError):
    pass


class BudgetExhausted(ApiFootballError):
    pass


class ApiFootballClient:
    def __init__(self, api_key: str, max_requests: int = 50, raw_dir: Path | None = None,
                 transport: httpx.BaseTransport | None = None, pause_seconds: float = 0.0) -> None:
        if not api_key:
            raise ApiFootballError("Falta API_FOOTBALL_KEY.")
        self._http = httpx.Client(base_url=BASE_URL, headers={"x-apisports-key": api_key},
                                  timeout=30.0, transport=transport)
        self.max_requests = max_requests
        self.used = 0
        self.remaining_today: int | None = None  # según cabecera del proveedor, si la envía
        self.raw_dir = raw_dir
        self.pause = pause_seconds

    def close(self) -> None:
        self._http.close()

    def get(self, endpoint: str, **params) -> dict:
        if self.used >= self.max_requests:
            raise BudgetExhausted(f"Presupuesto de {self.max_requests} consultas agotado en esta ejecución.")
        if self.remaining_today is not None and self.remaining_today <= 0:
            raise BudgetExhausted("El proveedor indica 0 consultas restantes hoy.")
        clean = {k: v for k, v in params.items() if v is not None}
        try:
            resp = self._http.get(endpoint, params=clean)
        except httpx.HTTPError as exc:
            raise ApiFootballError(f"Error de red en {endpoint}: {type(exc).__name__}") from exc
        self.used += 1
        rem = resp.headers.get("x-ratelimit-requests-remaining")
        if rem is not None and rem.isdigit():
            self.remaining_today = int(rem)
        if resp.status_code == 429:
            raise BudgetExhausted("Límite de solicitudes del proveedor alcanzado (HTTP 429).")
        if resp.status_code != 200:
            raise ApiFootballError(f"HTTP {resp.status_code} en {endpoint}")
        body = resp.json()
        errors = body.get("errors")
        if errors:  # la API devuelve 200 con errores en el cuerpo (lista o diccionario)
            raise ApiFootballError(f"La API respondió con errores en {endpoint}: {json.dumps(errors, ensure_ascii=False)[:300]}")
        if self.raw_dir is not None:
            self.raw_dir.mkdir(parents=True, exist_ok=True)
            tag = "_".join(f"{k}-{v}" for k, v in sorted(clean.items()))
            (self.raw_dir / f"{endpoint.strip('/').replace('/', '_')}__{tag}.json").write_text(
                json.dumps(body, ensure_ascii=False, indent=1), encoding="utf-8")
        if self.pause:
            time.sleep(self.pause)
        return body
