from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import projects
from app.configs.settings import get_settings
from app.database.session import init_db

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 应用启动时初始化数据库（创建表）
    init_db()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}


app.include_router(projects.router)
