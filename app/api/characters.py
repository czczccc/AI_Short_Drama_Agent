from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.providers.llm.base import LLMProvider
from app.providers.llm.factory import get_configured_llm_provider
from app.schemas.character import (
    CharacterBibleResponse,
    CharacterBibleUpdateRequest,
    CharacterGenerateRequest,
)
from app.schemas.common import ErrorResponse
from app.services.character_service import (
    CharacterBibleInputError,
    CharacterBiblesNotFoundError,
    generate_character_bibles,
    get_character_bibles,
    replace_character_bibles,
)
from app.services.outline_service import OutlineNotReadyError, ProjectNotFoundError


router = APIRouter(prefix="/projects", tags=["characters"])


def _raise_character_http_error(exc: Exception) -> None:
    if isinstance(exc, ProjectNotFoundError):
        raise HTTPException(status_code=404, detail="Project not found") from exc
    if isinstance(exc, OutlineNotReadyError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Project outline is not ready",
        ) from exc
    if isinstance(exc, CharacterBiblesNotFoundError):
        raise HTTPException(
            status_code=404,
            detail="Character bibles not found",
        ) from exc
    if isinstance(exc, CharacterBibleInputError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Character bibles do not match the project outline",
        ) from exc
    raise exc


@router.post(
    "/{project_id}/characters/generate",
    response_model=CharacterBibleResponse,
    responses={
        404: {"model": ErrorResponse, "description": "项目不存在"},
        409: {"model": ErrorResponse, "description": "项目大纲尚未就绪"},
        500: {"model": ErrorResponse, "description": "数据库操作失败"},
        502: {"model": ErrorResponse, "description": "LLM 调用或响应无效"},
        503: {"model": ErrorResponse, "description": "LLM Provider 配置不可用"},
    },
)
def create_character_bibles(
    project_id: int,
    payload: CharacterGenerateRequest,
    db: Annotated[Session, Depends(get_db)],
    llm_provider: Annotated[LLMProvider, Depends(get_configured_llm_provider)],
) -> CharacterBibleResponse:
    del payload
    try:
        return generate_character_bibles(db, project_id, llm_provider)
    except (ProjectNotFoundError, OutlineNotReadyError) as exc:
        _raise_character_http_error(exc)


@router.get(
    "/{project_id}/characters",
    response_model=CharacterBibleResponse,
    responses={
        404: {"model": ErrorResponse, "description": "项目或角色圣经不存在"},
        409: {"model": ErrorResponse, "description": "项目大纲尚未就绪"},
        500: {"model": ErrorResponse, "description": "数据库操作失败"},
    },
)
def read_character_bibles(
    project_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> CharacterBibleResponse:
    try:
        return get_character_bibles(db, project_id)
    except (
        ProjectNotFoundError,
        OutlineNotReadyError,
        CharacterBiblesNotFoundError,
    ) as exc:
        _raise_character_http_error(exc)


@router.put(
    "/{project_id}/characters",
    response_model=CharacterBibleResponse,
    responses={
        404: {"model": ErrorResponse, "description": "项目不存在"},
        409: {"model": ErrorResponse, "description": "项目大纲尚未就绪"},
        422: {"model": ErrorResponse, "description": "角色圣经校验失败"},
        500: {"model": ErrorResponse, "description": "数据库操作失败"},
    },
)
def update_character_bibles(
    project_id: int,
    payload: CharacterBibleUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
) -> CharacterBibleResponse:
    try:
        return replace_character_bibles(db, project_id, payload)
    except (
        ProjectNotFoundError,
        OutlineNotReadyError,
        CharacterBibleInputError,
    ) as exc:
        _raise_character_http_error(exc)
