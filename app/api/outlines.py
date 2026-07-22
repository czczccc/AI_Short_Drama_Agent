from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.providers.llm.base import LLMProvider
from app.providers.llm.factory import get_configured_llm_provider
from app.schemas.common import ErrorResponse
from app.schemas.outline import OutlineGenerateRequest, OutlineGenerateResponse
from app.services.outline_service import ProjectNotFoundError, generate_outline


router = APIRouter(prefix="/projects", tags=["outlines"])


@router.post(
    "/{project_id}/outline",
    response_model=OutlineGenerateResponse,
    responses={
        404: {"model": ErrorResponse, "description": "项目不存在"},
        500: {"model": ErrorResponse, "description": "数据库操作失败"},
        502: {"model": ErrorResponse, "description": "LLM 调用或响应无效"},
        503: {"model": ErrorResponse, "description": "LLM Provider 配置不可用"},
    },
)
def create_outline(
    project_id: int,
    payload: OutlineGenerateRequest,
    db: Annotated[Session, Depends(get_db)],
    llm_provider: Annotated[LLMProvider, Depends(get_configured_llm_provider)],
) -> OutlineGenerateResponse:
    try:
        return generate_outline(db, project_id, payload, llm_provider)
    except ProjectNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        ) from exc
