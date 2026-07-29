from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.providers.llm.base import LLMProvider
from app.providers.llm.factory import get_configured_llm_provider
from app.schemas.common import ErrorResponse
from app.schemas.showrunner import ShowrunnerGenerateRequest, ShowrunnerResponse
from app.services.character_service import CharacterBiblesNotFoundError
from app.services.outline_service import OutlineNotReadyError, ProjectNotFoundError
from app.services.showrunner_service import (
    ShowrunnerStateNotFoundError,
    generate_showrunner_state,
    get_showrunner_state,
)


router = APIRouter(prefix="/projects", tags=["showrunner"])


def _raise_showrunner_http_error(exc: Exception) -> None:
    if isinstance(exc, ProjectNotFoundError):
        raise HTTPException(status_code=404, detail="Project not found") from exc
    if isinstance(exc, OutlineNotReadyError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Project outline is not ready",
        ) from exc
    if isinstance(exc, CharacterBiblesNotFoundError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Character bibles are not ready",
        ) from exc
    if isinstance(exc, ShowrunnerStateNotFoundError):
        raise HTTPException(
            status_code=404,
            detail="Showrunner state not found",
        ) from exc
    raise exc


@router.post(
    "/{project_id}/showrunner",
    response_model=ShowrunnerResponse,
    responses={
        404: {"model": ErrorResponse, "description": "项目不存在"},
        409: {"model": ErrorResponse, "description": "项目大纲或角色圣经尚未就绪"},
        500: {"model": ErrorResponse, "description": "数据库操作失败"},
        502: {"model": ErrorResponse, "description": "LLM 调用或响应无效"},
        503: {"model": ErrorResponse, "description": "LLM Provider 配置不可用"},
    },
)
def create_showrunner_state(
    project_id: int,
    payload: ShowrunnerGenerateRequest,
    db: Annotated[Session, Depends(get_db)],
    llm_provider: Annotated[LLMProvider, Depends(get_configured_llm_provider)],
) -> ShowrunnerResponse:
    del payload
    try:
        return generate_showrunner_state(db, project_id, llm_provider)
    except (
        ProjectNotFoundError,
        OutlineNotReadyError,
        CharacterBiblesNotFoundError,
    ) as exc:
        _raise_showrunner_http_error(exc)


@router.get(
    "/{project_id}/showrunner",
    response_model=ShowrunnerResponse,
    responses={
        404: {"model": ErrorResponse, "description": "项目或 Showrunner State 不存在"},
        500: {"model": ErrorResponse, "description": "数据库操作失败"},
    },
)
def read_showrunner_state(
    project_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> ShowrunnerResponse:
    try:
        return get_showrunner_state(db, project_id)
    except (ProjectNotFoundError, ShowrunnerStateNotFoundError) as exc:
        _raise_showrunner_http_error(exc)

