from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.api import outlines, projects
from app.configs.settings import get_settings
from app.database.session import init_db
from app.providers.llm.base import (
    LLMCallError,
    LLMConfigurationError,
    LLMResponseJSONError,
    LLMResponseValidationError,
)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 应用启动时初始化数据库（创建表）
    init_db()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)


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


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}


app.include_router(projects.router)
app.include_router(outlines.router)
