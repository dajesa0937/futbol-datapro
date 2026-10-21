"""Persistencia del historial de análisis (SQLAlchemy: SQLite en desarrollo, PostgreSQL en producción).

Cada análisis guardado es una versión inmutable con su hora de publicación y los datos usados,
base para comparar después predicción vs resultado real.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text, create_engine, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class AnalysisRecord(Base):
    __tablename__ = "analysis_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    home: Mapped[str] = mapped_column(String(80), index=True)
    away: Mapped[str] = mapped_column(String(80), index=True)
    match_date: Mapped[str] = mapped_column(String(10))
    model_version: Mapped[str] = mapped_column(String(40))
    source_name: Mapped[str] = mapped_column(String(120))
    is_demo: Mapped[int] = mapped_column(Integer, default=0)
    p_home: Mapped[float | None] = mapped_column(nullable=True)
    p_draw: Mapped[float | None] = mapped_column(nullable=True)
    p_away: Mapped[float | None] = mapped_column(nullable=True)
    payload: Mapped[str] = mapped_column(Text)  # análisis completo en JSON


class HistoryStore:
    def __init__(self, database_url: str, max_rows: int = 1000) -> None:
        kwargs = {"connect_args": {"check_same_thread": False}} if database_url.startswith("sqlite") else {}
        self.engine = create_engine(database_url, future=True, **kwargs)
        Base.metadata.create_all(self.engine)
        self._session = sessionmaker(self.engine, expire_on_commit=False)
        self.max_rows = max_rows

    def count(self) -> int:
        with self._session() as s:
            return s.scalar(select(func.count(AnalysisRecord.id))) or 0

    def save(self, analysis: dict) -> int:
        if self.count() >= self.max_rows:
            raise HistoryFull(f"Límite de {self.max_rows} análisis guardados alcanzado.")
        pred = analysis.get("prediction") or {}
        src = analysis.get("source") or {}
        rec = AnalysisRecord(
            home=analysis["match"]["home"], away=analysis["match"]["away"],
            match_date=analysis["match"]["date"],
            model_version=(analysis.get("model") or {}).get("version", "n/d"),
            source_name=src.get("name", "n/d"), is_demo=int(bool(src.get("is_demo"))),
            p_home=pred.get("p_home"), p_draw=pred.get("p_draw"), p_away=pred.get("p_away"),
            payload=json.dumps(analysis, ensure_ascii=False),
        )
        with self._session() as s:
            s.add(rec)
            s.commit()
            return rec.id

    def list(self, limit: int = 50) -> list[dict]:
        with self._session() as s:
            rows = s.scalars(select(AnalysisRecord).order_by(AnalysisRecord.id.desc()).limit(limit)).all()
            return [self._summary(r) for r in rows]

    def get(self, rec_id: int) -> dict | None:
        with self._session() as s:
            rec = s.get(AnalysisRecord, rec_id)
            if rec is None:
                return None
            return self._summary(rec) | {"analysis": json.loads(rec.payload)}

    @staticmethod
    def _summary(r: AnalysisRecord) -> dict:
        return {"id": r.id, "created_at": r.created_at.isoformat(), "home": r.home, "away": r.away,
                "match_date": r.match_date, "model_version": r.model_version, "source_name": r.source_name,
                "is_demo": bool(r.is_demo), "p_home": r.p_home, "p_draw": r.p_draw, "p_away": r.p_away}


class HistoryFull(RuntimeError):
    pass
