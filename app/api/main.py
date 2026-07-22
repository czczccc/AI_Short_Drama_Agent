from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api import outlines, projects, scripts
from app.configs.settings import get_settings
from app.database.session import init_db
from app.providers.llm.base import (
    LLMCallError,
    LLMConfigurationError,
    LLMResponseJSONError,
    LLMResponseValidationError,
)

settings = get_settings()
API_V1_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 应用启动时初始化数据库（创建表）
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="AI 短剧后端 API：项目、大纲与单集剧本生成。",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.exception_handler(LLMConfigurationError)
async def handle_llm_configuration_error(
    request: Request, exc: LLMConfigurationError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "LLM 服务配置不可用"},
    )


@app.exception_handler(LLMCallError)
async def handle_llm_call_error(request: Request, exc: LLMCallError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"detail": "LLM 服务调用失败"},
    )


@app.exception_handler(LLMResponseJSONError)
async def handle_llm_json_error(
    request: Request, exc: LLMResponseJSONError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"detail": "LLM 返回格式无效"},
    )


@app.exception_handler(LLMResponseValidationError)
async def handle_llm_validation_error(
    request: Request, exc: LLMResponseValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"detail": "LLM 返回结构无效"},
    )


@app.exception_handler(SQLAlchemyError)
async def handle_database_error(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "数据库操作失败"},
    )


@app.get(f"{API_V1_PREFIX}/health", tags=["health"])
def health_check() -> dict:
    return {"status": "ok"}


@app.get("/health", include_in_schema=False)
def legacy_health_check() -> dict:
    return health_check()


api_v1_router = APIRouter(prefix=API_V1_PREFIX)
api_v1_router.include_router(projects.router)
api_v1_router.include_router(outlines.router)
api_v1_router.include_router(scripts.router)
app.include_router(api_v1_router)

# 暂时保留旧路径，避免已有调用方立即中断；正式 OpenAPI 只公布 /api/v1。
app.include_router(projects.router, include_in_schema=False)
app.include_router(outlines.router, include_in_schema=False)
app.include_router(scripts.router, include_in_schema=False)
