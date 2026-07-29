from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


def utcnow() -> datetime:
    """返回 UTC 当前时间的朴素（naive）datetime，用于 SQLAlchemy DateTime 默认值。"""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")
    idea: Mapped[str | None] = mapped_column(Text, nullable=True)
    outline_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    characters_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    scripts_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    memory_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    showrunner_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utcnow, onupdate=utcnow
    )
