import json
import time

from sqlalchemy.orm import Session

from app.agents.writer import WriterAgent
from app.agents.qc import QCAgent
from app.models.project import Project
from app.observability.logging import duration_ms, log_event
from app.providers.llm.base import LLMProvider
from app.schemas.outline import EpisodeOutline, StoryOutline
from app.schemas.script import EpisodeScript, ScriptGenerateRequest, ScriptResponse
from app.services.character_service import load_character_bibles
from app.services.memory_service import load_story_memory, upsert_episode_memory
from app.services.outline_service import (
    OutlineNotReadyError,
    ProjectNotFoundError,
    load_outline,
)
from app.services.project_service import get_project
from app.services.showrunner_service import (
    ShowrunnerEpisodeNotFoundError,
    ShowrunnerStateNotFoundError,
    WriterBriefNotFoundError,
    get_writer_brief,
    save_showrunner_qc_report,
)


class EpisodeNotFoundError(Exception):
    """Requested episode is not present in the project outline."""


class ScriptNotFoundError(Exception):
    """Requested episode script has not been generated."""


class ShowrunnerQCRequiresBriefError(Exception):
    """Showrunner QC requires the script to be generated with a Writer Brief."""


class ShowrunnerQCNotPassedError(Exception):
    """Showrunner QC blocked the draft from becoming the official script."""


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
    if data.run_showrunner_qc and not data.use_showrunner_brief:
        raise ShowrunnerQCRequiresBriefError

    character_collection = load_character_bibles(project, outline)
    story_memory = load_story_memory(project)
    writer_brief = None
    if data.use_showrunner_brief:
        writer_brief = get_writer_brief(db, project_id, episode_number).brief

    started_at = time.perf_counter()
    log_event(
        "workflow.script.started",
        project_id=project_id,
        episode_number=episode_number,
        use_showrunner_brief=data.use_showrunner_brief,
        run_showrunner_qc=data.run_showrunner_qc,
        target_duration_seconds=data.target_duration_seconds,
    )
    script = WriterAgent(llm_provider).generate_script(
        story_outline=outline,
        episode_outline=episode_outline,
        target_duration_seconds=data.target_duration_seconds,
        character_bibles=(
            character_collection.characters if character_collection else None
        ),
        story_memory=story_memory,
        writer_brief=writer_brief,
    )
    log_event(
        "workflow.script.draft_generated",
        project_id=project_id,
        episode_number=episode_number,
        scene_count=len(script.scenes),
        duration_ms=duration_ms(started_at),
    )

    if data.run_showrunner_qc:
        qc_started_at = time.perf_counter()
        qc_report = QCAgent(llm_provider).generate_report(
            story_outline=outline,
            episode_outline=episode_outline,
            script=script,
            character_bibles=(
                character_collection.characters if character_collection else None
            ),
            story_memory=story_memory,
            writer_brief=writer_brief,
        )
        save_showrunner_qc_report(project, episode_number, qc_report)
        if qc_report.status != "pass":
            db.commit()
            log_event(
                "workflow.showrunner_qc.blocked",
                level="warning",
                project_id=project_id,
                episode_number=episode_number,
                qc_status=qc_report.status,
                issue_count=len(qc_report.issues),
                duration_ms=duration_ms(qc_started_at),
            )
            raise ShowrunnerQCNotPassedError
        log_event(
            "workflow.showrunner_qc.passed",
            project_id=project_id,
            episode_number=episode_number,
            issue_count=len(qc_report.issues),
            duration_ms=duration_ms(qc_started_at),
        )

    scripts = json.loads(project.scripts_json) if project.scripts_json else {}
    scripts[str(episode_number)] = script.model_dump(mode="json")
    project.scripts_json = json.dumps(scripts, ensure_ascii=False)
    upsert_episode_memory(project, script)
    project.status = "script_ready"
    db.commit()
    db.refresh(project)
    log_event(
        "workflow.script.saved",
        project_id=project.id,
        episode_number=episode_number,
        status=project.status,
    )

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
