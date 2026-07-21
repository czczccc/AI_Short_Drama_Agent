"""Pytest 公共配置：测试数据库隔离。

测试使用独立的临时 SQLite 数据库，通过 FastAPI 依赖注入覆盖正式数据库会话，
不读取也不写入正式 app.db。测试会话结束后临时库自动删除。
"""
import hashlib
import shutil
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.main import app
from app.database.base import Base
from app.database.session import get_db
from app.models import project  # noqa: F401  # 注册模型到 Base.metadata


def _file_digest(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture(scope="session")
def formal_db_snapshot() -> str | None:
    """记录正式数据库内容，用于证明测试过程没有改写它。"""
    formal_db = Path("app.db")
    snapshot = _file_digest(formal_db)
    yield snapshot
    assert _file_digest(formal_db) == snapshot


@pytest.fixture(scope="session")
def test_engine():
    """创建独立的临时 SQLite 数据库（会话级），测试结束后自动删除。"""
    tmp_dir = Path(tempfile.mkdtemp(prefix="asd_test_db_"))
    db_file = tmp_dir / "test_app.db"
    engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()
    shutil.rmtree(tmp_dir, ignore_errors=True)


@pytest.fixture(scope="session")
def test_session_local(test_engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def _override_db(test_session_local):
    """用依赖注入覆盖正式 get_db，使所有测试请求走临时数据库。"""
    def _get_test_db():
        db = test_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def client(_override_db) -> TestClient:
    """共享的 FastAPI 测试客户端（不触发 lifespan，不触碰正式 app.db）。"""
    return TestClient(app)
