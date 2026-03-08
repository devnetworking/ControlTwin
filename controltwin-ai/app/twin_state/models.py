from datetime import datetime
from sqlalchemy import String, DateTime, Integer, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TwinState(Base):
    __tablename__ = "twin_states"

    asset_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    reported_state: Mapped[dict] = mapped_column(JSONB, default=dict)
    desired_state: Mapped[dict] = mapped_column(JSONB, default=dict)
    last_reported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_desired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    divergences: Mapped[list] = mapped_column(JSONB, default=list)
    llm_explanation: Mapped[str | None] = mapped_column(String, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class StateHistory(Base):
    __tablename__ = "state_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    asset_id: Mapped[str] = mapped_column(String(128), index=True)
    state_type: Mapped[str] = mapped_column(String(32))
    state: Mapped[dict] = mapped_column(JSONB, default=dict)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    source: Mapped[str | None] = mapped_column(String(128), nullable=True)
