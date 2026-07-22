from collections.abc import Iterator

from sqlalchemy import Engine, create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from app.configs.settings import get_settings
from app.database.base import Base

settings = get_settings()

_connect_args = (
    {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)
engine = create_engine(settings.database_url, connect_args=_connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    # 导入模型以注册到 Base.metadata，然后创建所有表
    from app.models import project  # noqa: F401

    Base.metadata.create_all(bind=engine)
    ensure_project_characters_json_column(engine)


def ensure_project_characters_json_column(target_engine: Engine) -> None:
    """为已有 SQLite 项目库幂等增加 Phase 2C JSON 字段。"""
    if target_engine.dialect.name != "sqlite":
        return

    inspector = inspect(target_engine)
    if "projects" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("projects")}
    if "characters_json" in columns:
        return

    with target_engine.begin() as connection:
        connection.execute(text("ALTER TABLE projects ADD COLUMN characters_json TEXT"))
