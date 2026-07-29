import hashlib
import json

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.agents.showrunner import ShowrunnerAgent
from app.models.project import Project
from app.providers.llm.base import LLMProvider, LLMResponseValidationError
from app.schemas.showrunner import ShowrunnerResponse, ShowrunnerState
from app.services.character_service import (
    CharacterBiblesNotFoundError,
    load_character_bibles,
)
from app.services.outline_service import ProjectNotFoundError, load_outline
from app.services.project_service import get_project


class ShowrunnerStateNotFoundError(Exception):
    """Project does not have a generated Showrunner State."""


def stable_json_sha256(value: object) -> str:
    serialized = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _response(project: Project, state: ShowrunnerState) -> ShowrunnerResponse:
    return ShowrunnerResponse(project_id=project.id, showrunner=state)


def load_showrunner_state(project: Project) -> ShowrunnerState:
    if not project.showrunner_json:
        raise ShowrunnerStateNotFoundError
    try:
        return ShowrunnerState.model_validate_json(project.showrunner_json)
    except (ValidationError, ValueError) as exc:
        raise ShowrunnerStateNotFoundError from exc


def generate_showrunner_state(
    db: Session,
    project_id: int,
    llm_provider: LLMProvider,
) -> ShowrunnerResponse:
    project = get_project(db, project_id)
    if project is None:
        raise ProjectNotFoundError

    outline = load_outline(project)
    characters = load_character_bibles(project, outline)
    if characters is None:
        raise CharacterBiblesNotFoundError

    outline_data = outline.model_dump(mode="json")
    characters_data = {
        character_id: bible.model_dump(mode="json")
        for character_id, bible in characters.characters.items()
    }
    source_outline_hash = stable_json_sha256(outline_data)
    source_characters_hash = stable_json_sha256(characters_data)

    state = ShowrunnerAgent(llm_provider).generate_showrunner_state(
        outline=outline,
        characters=characters,
        source_outline_hash=source_outline_hash,
        source_characters_hash=source_characters_hash,
    )
    expected_character_ids = set(characters.characters)
    arc_character_ids = [arc.character_id for arc in state.character_arcs]
    if len(arc_character_ids) != len(set(arc_character_ids)) or set(
        arc_character_ids
    ) != expected_character_ids:
        raise LLMResponseValidationError("Showrunner character arcs do not match")

    state = ShowrunnerState.model_validate(
        {
            **state.model_dump(mode="json"),
            "source_outline_hash": source_outline_hash,
            "source_characters_hash": source_characters_hash,
            "writer_briefs": {},
            "qc_reports": {},
        }
    )

    project.showrunner_json = state.model_dump_json()
    db.commit()
    db.refresh(project)
    return _response(project, state)


def get_showrunner_state(db: Session, project_id: int) -> ShowrunnerResponse:
    project = get_project(db, project_id)
    if project is None:
        raise ProjectNotFoundError
    state = load_showrunner_state(project)
    return _response(project, state)
