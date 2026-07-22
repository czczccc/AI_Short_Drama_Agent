import json

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.agents.character import CharacterAgent
from app.models.project import Project
from app.providers.llm.base import LLMProvider
from app.schemas.character import (
    CharacterBibleCollection,
    CharacterBibleResponse,
    CharacterBibleUpdateRequest,
)
from app.schemas.outline import StoryOutline
from app.services.outline_service import ProjectNotFoundError, load_outline
from app.services.project_service import get_project


class CharacterBiblesNotFoundError(Exception):
    """Project does not have generated character bibles."""


class CharacterBibleInputError(Exception):
    """User-submitted character bibles conflict with the project outline."""


def _response(
    project: Project, collection: CharacterBibleCollection
) -> CharacterBibleResponse:
    return CharacterBibleResponse(
        project_id=project.id,
        status=project.status,
        characters=collection.characters,
    )


def _save_collection(
    db: Session, project: Project, collection: CharacterBibleCollection
) -> CharacterBibleResponse:
    project.characters_json = json.dumps(
        {
            character_id: bible.model_dump(mode="json")
            for character_id, bible in collection.characters.items()
        },
        ensure_ascii=False,
    )
    project.status = "characters_ready"
    db.commit()
    db.refresh(project)
    return _response(project, collection)


def load_character_bibles(
    project: Project, outline: StoryOutline
) -> CharacterBibleCollection | None:
    if not project.characters_json:
        return None
    stored = json.loads(project.characters_json)
    return CharacterBibleCollection.model_validate(
        {"characters": stored},
        context={"outline_characters": outline.characters},
    )


def generate_character_bibles(
    db: Session,
    project_id: int,
    llm_provider: LLMProvider,
) -> CharacterBibleResponse:
    project = get_project(db, project_id)
    if project is None:
        raise ProjectNotFoundError
    outline = load_outline(project)
    collection = CharacterAgent(llm_provider).generate_character_bibles(outline)
    return _save_collection(db, project, collection)


def get_character_bibles(db: Session, project_id: int) -> CharacterBibleResponse:
    project = get_project(db, project_id)
    if project is None:
        raise ProjectNotFoundError
    outline = load_outline(project)
    collection = load_character_bibles(project, outline)
    if collection is None:
        raise CharacterBiblesNotFoundError
    return _response(project, collection)


def replace_character_bibles(
    db: Session,
    project_id: int,
    data: CharacterBibleUpdateRequest,
) -> CharacterBibleResponse:
    project = get_project(db, project_id)
    if project is None:
        raise ProjectNotFoundError
    outline = load_outline(project)
    try:
        collection = CharacterBibleCollection.model_validate(
            data.model_dump(mode="json"),
            context={"outline_characters": outline.characters},
        )
    except ValidationError as exc:
        raise CharacterBibleInputError from exc
    return _save_collection(db, project, collection)
