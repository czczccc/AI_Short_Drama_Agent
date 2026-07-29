from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.providers.llm.base import LLMProvider
from app.providers.llm.factory import get_configured_llm_provider
from app.schemas.common import ErrorResponse
from app.schemas.script import ScriptGenerateRequest, ScriptResponse
from app.services.outline_service import OutlineNotReadyError, ProjectNotFoundError
from app.services.script_service import (
    EpisodeNotFoundError,
    ScriptNotFoundError,
    ShowrunnerQCNotPassedError,
    ShowrunnerQCRequiresBriefError,
    generate_script,
    get_script,
)
from app.services.showrunner_service import (
    ShowrunnerEpisodeNotFoundError,
    ShowrunnerStateNotFoundError,
    WriterBriefNotFoundError,
)


router = APIRouter(prefix="/projects", tags=["scripts"])


def _raise_script_http_error(exc: Exception) -> None:
    if isinstance(exc, ProjectNotFoundError):
        raise HTTPException(status_code=404, detail="Project not found") from exc
    if isinstance(exc, OutlineNotReadyError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Project outline is not ready",
        ) from exc
    if isinstance(exc, EpisodeNotFoundError):
        raise HTTPException(status_code=404, detail="Episode not found") from exc
    if isinstance(exc, ScriptNotFoundError):
        raise HTTPException(status_code=404, detail="Script not found") from exc
    if isinstance(exc, ShowrunnerStateNotFoundError):
        raise HTTPException(status_code=404, detail="Showrunner state not found") from exc
    if isinstance(exc, ShowrunnerEpisodeNotFoundError):
        raise HTTPException(
            status_code=404,
            detail="Episode not found in showrunner plan",
        ) from exc
    if isinstance(exc, WriterBriefNotFoundError):
        raise HTTPException(status_code=404, detail="Writer brief not found") from exc
    if isinstance(exc, ShowrunnerQCRequiresBriefError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Showrunner QC requires writer brief",
        ) from exc
    if isinstance(exc, ShowrunnerQCNotPassedError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Showrunner QC did not pass",
        ) from exc
    raise exc


@router.post(
    "/{project_id}/episodes/{episode_number}/script",
    response_model=ScriptResponse,
    responses={
        404: {"model": ErrorResponse, "description": "项目或分集不存在"},
        409: {"model": ErrorResponse, "description": "项目大纲尚未就绪"},
        500: {"model": ErrorResponse, "description": "数据库操作失败"},
        502: {"model": ErrorResponse, "description": "LLM 调用或响应无效"},
        503: {"model": ErrorResponse, "description": "LLM Provider 配置不可用"},
    },
)
def create_script(
    project_id: int,
    episode_number: int,
    payload: ScriptGenerateRequest,
    db: Annotated[Session, Depends(get_db)],
    llm_provider: Annotated[LLMProvider, Depends(get_configured_llm_provider)],
) -> ScriptResponse:
    try:
        return generate_script(
            db,
            project_id,
            episode_number,
            payload,
            llm_provider,
        )
    except (
        ProjectNotFoundError,
        OutlineNotReadyError,
        EpisodeNotFoundError,
        ShowrunnerStateNotFoundError,
        ShowrunnerEpisodeNotFoundError,
        WriterBriefNotFoundError,
        ShowrunnerQCRequiresBriefError,
        ShowrunnerQCNotPassedError,
    ) as exc:
        _raise_script_http_error(exc)


@router.get(
    "/{project_id}/episodes/{episode_number}/script",
    response_model=ScriptResponse,
    responses={
        404: {"model": ErrorResponse, "description": "项目、分集或剧本不存在"},
        409: {"model": ErrorResponse, "description": "项目大纲尚未就绪"},
        500: {"model": ErrorResponse, "description": "数据库操作失败"},
    },
)
def read_script(
    project_id: int,
    episode_number: int,
    db: Annotated[Session, Depends(get_db)],
) -> ScriptResponse:
    try:
        return get_script(db, project_id, episode_number)
    except (
        ProjectNotFoundError,
        OutlineNotReadyError,
        EpisodeNotFoundError,
        ScriptNotFoundError,
    ) as exc:
        _raise_script_http_error(exc)
