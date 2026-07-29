from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.agents.director import DirectorAgent
from app.models.project import Project
from app.observability.logging import log_event
from app.providers.llm.base import LLMProvider
from app.schemas.outline import (
    OutlineGenerateRequest,
    OutlineGenerateResponse,
    StoryOutline,
)
from app.services.project_service import get_project


class ProjectNotFoundError(Exception):
    """Requested project does not exist."""


class OutlineNotReadyError(Exception):
    """Project has no valid outline yet."""


def load_outline(project: Project) -> StoryOutline:
    if not project.outline_json:
        raise OutlineNotReadyError
    try:
        return StoryOutline.model_validate_json(project.outline_json)
    except (ValidationError, ValueError) as exc:
        raise OutlineNotReadyError from exc


def generate_outline(
    db: Session,
    project_id: int,
    data: OutlineGenerateRequest,
    llm_provider: LLMProvider,
) -> OutlineGenerateResponse:
    project = get_project(db, project_id)
    if project is None:
        raise ProjectNotFoundError

    log_event(
        "workflow.outline.started",
        project_id=project_id,
        episode_count=data.episode_count,
    )
    outline = DirectorAgent(llm_provider).generate_outline(
        idea=data.idea,
        episode_count=data.episode_count,
    )
    project.idea = data.idea
    project.outline_json = outline.model_dump_json()
    project.status = "outline_ready"
    db.commit()
    db.refresh(project)
    log_event(
        "workflow.outline.generated",
        project_id=project.id,
        episode_count=len(outline.episodes),
        status=project.status,
    )

    return OutlineGenerateResponse(
        project_id=project.id,
        status=project.status,
        outline=outline,
    )
