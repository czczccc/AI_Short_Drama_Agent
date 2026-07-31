import json

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.agents.qc import QCAgent
from app.providers.llm.base import LLMProvider
from app.schemas.qc import QCReport
from app.schemas.script import EpisodeScript
from app.services.character_service import load_character_bibles
from app.services.continuity_qc import evaluate_script_rules, merge_qc_report
from app.services.memory_service import load_story_memory
from app.services.outline_service import (
    ProjectNotFoundError,
    load_outline,
)
from app.services.project_service import get_project
from app.services.script_service import (
    ScriptNotFoundError,
    _find_episode,
)


def generate_episode_qc(
    db: Session,
    project_id: int,
    episode_number: int,
    llm_provider: LLMProvider,
) -> QCReport:
    project = get_project(db, project_id)
    if project is None:
        raise ProjectNotFoundError

    outline = load_outline(project)
    episode_outline = _find_episode(outline, episode_number)
    scripts = json.loads(project.scripts_json) if project.scripts_json else {}
    stored_script = scripts.get(str(episode_number))
    if stored_script is None:
        raise ScriptNotFoundError

    try:
        script = EpisodeScript.model_validate(
            stored_script,
            context={
                "expected_episode_number": episode_outline.episode_number,
                "allowed_character_ids": {
                    character.character_id for character in outline.characters
                },
            },
        )
    except ValidationError as exc:
        raise ScriptNotFoundError from exc

    character_collection = load_character_bibles(project, outline)
    rule_issues = evaluate_script_rules(
        script,
        target_duration_seconds=script.duration_seconds,
    )
    report = QCAgent(llm_provider).generate_report(
        story_outline=outline,
        episode_outline=episode_outline,
        script=script,
        character_bibles=(
            character_collection.characters if character_collection else None
        ),
        story_memory=load_story_memory(project),
        rule_issues=rule_issues,
    )
    return merge_qc_report(report, rule_issues)
