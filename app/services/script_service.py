import json

from sqlalchemy.orm import Session

from app.agents.writer import WriterAgent
from app.models.project import Project
from app.providers.llm.base import LLMProvider
from app.schemas.outline import EpisodeOutline, StoryOutline
from app.schemas.script import EpisodeScript, ScriptGenerateRequest, ScriptResponse
from app.services.character_service import load_character_bibles
from app.services.outline_service import (
    OutlineNotReadyError,
    ProjectNotFoundError,
    load_outline,
)
from app.services.project_service import get_project


class EpisodeNotFoundError(Exception):
    """Requested episode is not present in the project outline."""


class ScriptNotFoundError(Exception):
    """Requested episode script has not been generated."""


def _find_episode(outline: StoryOutline, episode_number: int) -> EpisodeOutline:
    episode = next(
        (
            item
            for item in outline.episodes
            if item.episode_number == episode_number
        ),
        None,
    )
    if episode is None:
        raise EpisodeNotFoundError
    return episode


def generate_script(
    db: Session,
    project_id: int,
    episode_number: int,
    data: ScriptGenerateRequest,
    llm_provider: LLMProvider,
) -> ScriptResponse:
    project = get_project(db, project_id)
    if project is None:
        raise ProjectNotFoundError

    outline = load_outline(project)
    episode_outline = _find_episode(outline, episode_number)
    character_collection = load_character_bibles(project, outline)
    script = WriterAgent(llm_provider).generate_script(
        story_outline=outline,
        episode_outline=episode_outline,
        target_duration_seconds=data.target_duration_seconds,
        character_bibles=(
            character_collection.characters if character_collection else None
        ),
    )

    scripts = json.loads(project.scripts_json) if project.scripts_json else {}
    scripts[str(episode_number)] = script.model_dump(mode="json")
    project.scripts_json = json.dumps(scripts, ensure_ascii=False)
    project.status = "script_ready"
    db.commit()
    db.refresh(project)

    return ScriptResponse(
        project_id=project.id,
        episode_number=episode_number,
        status=project.status,
        script=script,
    )


def get_script(db: Session, project_id: int, episode_number: int) -> ScriptResponse:
    project = get_project(db, project_id)
    if project is None:
        raise ProjectNotFoundError

    outline = load_outline(project)
    episode_outline = _find_episode(outline, episode_number)
    scripts = json.loads(project.scripts_json) if project.scripts_json else {}
    stored_script = scripts.get(str(episode_number))
    if stored_script is None:
        raise ScriptNotFoundError

    script = EpisodeScript.model_validate(
        stored_script,
        context={
            "expected_episode_number": episode_outline.episode_number,
            "allowed_character_ids": {
                character.character_id for character in outline.characters
            },
        },
    )
    return ScriptResponse(
        project_id=project.id,
        episode_number=episode_number,
        status=project.status,
        script=script,
    )
