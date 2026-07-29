import json
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.project import Project
from app.observability.logging import read_recent_logs
from app.providers.llm.base import LLMProvider
from app.providers.llm.factory import get_configured_llm_provider
from app.services.memory_service import load_story_memory
from app.services.outline_service import OutlineNotReadyError, ProjectNotFoundError
from app.services.qc_service import generate_episode_qc
from app.services.script_service import EpisodeNotFoundError, ScriptNotFoundError

router = APIRouter(prefix="/dev", tags=["dev"])
TESTBENCH_PATH = Path(__file__).resolve().parents[1] / "dev" / "testbench.html"


@router.get("/testbench", response_class=HTMLResponse, include_in_schema=False)
def get_testbench() -> HTMLResponse:
    return HTMLResponse(TESTBENCH_PATH.read_text(encoding="utf-8"))


def _loads_json(value: str | None, default):
    if not value:
        return default
    return json.loads(value)


def _project_summary(project: Project) -> dict:
    scripts = _loads_json(project.scripts_json, {})
    return {
        "id": project.id,
        "name": project.name,
        "status": project.status,
        "idea": project.idea,
        "saved_episode_numbers": sorted(int(number) for number in scripts),
        "created_at": project.created_at.isoformat(),
        "updated_at": project.updated_at.isoformat(),
    }


@router.get("/projects", include_in_schema=False)
def list_dev_projects(db: Session = Depends(get_db)) -> dict:
    projects = db.scalars(
        select(Project).order_by(desc(Project.updated_at), desc(Project.id)).limit(50)
    ).all()
    return {"projects": [_project_summary(project) for project in projects]}


@router.get("/logs", include_in_schema=False)
def list_dev_logs(
    project_id: int | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
) -> dict:
    return {
        "logs": read_recent_logs(project_id=project_id, limit=limit),
    }


@router.get("/projects/{project_id}/state", include_in_schema=False)
def get_dev_project_state(project_id: int, db: Session = Depends(get_db)) -> dict:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    scripts = _loads_json(project.scripts_json, {})
    return {
        "project": _project_summary(project),
        "outline": _loads_json(project.outline_json, None),
        "characters": _loads_json(project.characters_json, None),
        "scripts": scripts,
        "memory": load_story_memory(project).model_dump(mode="json"),
        "saved_episode_numbers": sorted(int(number) for number in scripts),
    }


@router.delete("/projects/{project_id}", include_in_schema=False)
def delete_dev_project(project_id: int, db: Session = Depends(get_db)) -> dict:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    db.delete(project)
    db.commit()
    return {"deleted_project_id": project_id}


@router.post(
    "/projects/{project_id}/episodes/{episode_number}/qc",
    include_in_schema=False,
)
def generate_dev_episode_qc(
    project_id: int,
    episode_number: int,
    db: Annotated[Session, Depends(get_db)],
    llm_provider: Annotated[LLMProvider, Depends(get_configured_llm_provider)],
) -> dict:
    try:
        report = generate_episode_qc(db, project_id, episode_number, llm_provider)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc
    except OutlineNotReadyError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Project outline is not ready",
        ) from exc
    except EpisodeNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Episode not found") from exc
    except ScriptNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Script not found") from exc

    return {
        "project_id": project_id,
        "episode_number": episode_number,
        "report": report.model_dump(mode="json"),
    }
