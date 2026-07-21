from sqlalchemy.orm import Session

from app.agents.director import DirectorAgent
from app.models.project import Project
from app.providers.llm.base import LLMProvider
from app.schemas.outline import OutlineGenerateRequest, OutlineGenerateResponse
from app.services.project_service import get_project


class ProjectNotFoundError(Exception):
    """Requested project does not exist."""


def generate_outline(
    db: Session,
    project_id: int,
    data: OutlineGenerateRequest,
    llm_provider: LLMProvider,
) -> OutlineGenerateResponse:
    project = get_project(db, project_id)
    if project is None:
        raise ProjectNotFoundError

    outline = DirectorAgent(llm_provider).generate_outline(
        idea=data.idea,
        episode_count=data.episode_count,
    )
    project.idea = data.idea
    project.outline_json = outline.model_dump_json()
    project.status = "outline_ready"
    db.commit()
    db.refresh(project)

    return OutlineGenerateResponse(
        project_id=project.id,
        status=project.status,
        outline=outline,
    )
