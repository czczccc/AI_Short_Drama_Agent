from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.providers.llm.base import LLMProvider
from app.providers.llm.factory import get_configured_llm_provider
from app.schemas.common import ErrorResponse
from app.schemas.showrunner import (
    ShowrunnerGenerateRequest,
    ShowrunnerQCResponse,
    ShowrunnerResponse,
    WriterBriefGenerateRequest,
    WriterBriefResponse,
)
from app.services.character_service import CharacterBiblesNotFoundError
from app.services.outline_service import OutlineNotReadyError, ProjectNotFoundError
from app.services.showrunner_service import (
    ShowrunnerEpisodeNotFoundError,
    ShowrunnerQCReportNotFoundError,
    ShowrunnerStateNotFoundError,
    WriterBriefNotFoundError,
    generate_showrunner_state,
    generate_writer_brief,
    get_showrunner_state,
    get_showrunner_qc_report,
    get_writer_brief,
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
    if isinstance(exc, ShowrunnerEpisodeNotFoundError):
        raise HTTPException(
            status_code=404,
            detail="Episode not found in showrunner plan",
        ) from exc
    if isinstance(exc, WriterBriefNotFoundError):
        raise HTTPException(
            status_code=404,
            detail="Writer brief not found",
        ) from exc
    if isinstance(exc, ShowrunnerQCReportNotFoundError):
        raise HTTPException(
            status_code=404,
            detail="Showrunner QC report not found",
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


@router.post(
    "/{project_id}/episodes/{episode_number}/writer-brief",
    response_model=WriterBriefResponse,
    responses={
        404: {"model": ErrorResponse, "description": "项目、Showrunner State 或分集不存在"},
        422: {"model": ErrorResponse, "description": "请求参数错误"},
        500: {"model": ErrorResponse, "description": "数据库操作失败"},
        502: {"model": ErrorResponse, "description": "LLM 调用或响应无效"},
        503: {"model": ErrorResponse, "description": "LLM Provider 配置不可用"},
    },
)
def create_writer_brief(
    project_id: int,
    episode_number: int,
    payload: WriterBriefGenerateRequest,
    db: Annotated[Session, Depends(get_db)],
    llm_provider: Annotated[LLMProvider, Depends(get_configured_llm_provider)],
) -> WriterBriefResponse:
    _ = payload.force_regenerate
    try:
        return generate_writer_brief(
            db=db,
            project_id=project_id,
            episode_number=episode_number,
            target_duration_seconds=payload.target_duration_seconds,
            llm_provider=llm_provider,
        )
    except (
        ProjectNotFoundError,
        ShowrunnerStateNotFoundError,
        ShowrunnerEpisodeNotFoundError,
    ) as exc:
        _raise_showrunner_http_error(exc)


@router.get(
    "/{project_id}/episodes/{episode_number}/writer-brief",
    response_model=WriterBriefResponse,
    responses={
        404: {"model": ErrorResponse, "description": "项目、Showrunner State、分集或 Brief 不存在"},
        500: {"model": ErrorResponse, "description": "数据库操作失败"},
    },
)
def read_writer_brief(
    project_id: int,
    episode_number: int,
    db: Annotated[Session, Depends(get_db)],
) -> WriterBriefResponse:
    try:
        return get_writer_brief(db, project_id, episode_number)
    except (
        ProjectNotFoundError,
        ShowrunnerStateNotFoundError,
        ShowrunnerEpisodeNotFoundError,
        WriterBriefNotFoundError,
    ) as exc:
        _raise_showrunner_http_error(exc)


@router.get(
    "/{project_id}/episodes/{episode_number}/showrunner-qc",
    response_model=ShowrunnerQCResponse,
    responses={
        404: {"model": ErrorResponse, "description": "项目、Showrunner State、分集或 QC 报告不存在"},
        500: {"model": ErrorResponse, "description": "数据库操作失败"},
    },
)
def read_showrunner_qc_report(
    project_id: int,
    episode_number: int,
    db: Annotated[Session, Depends(get_db)],
) -> ShowrunnerQCResponse:
    try:
        return get_showrunner_qc_report(db, project_id, episode_number)
    except (
        ProjectNotFoundError,
        ShowrunnerStateNotFoundError,
        ShowrunnerEpisodeNotFoundError,
        ShowrunnerQCReportNotFoundError,
    ) as exc:
        _raise_showrunner_http_error(exc)
