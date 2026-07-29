import hashlib
import json

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.agents.showrunner import ShowrunnerAgent
from app.models.project import Project
from app.observability.logging import log_event
from app.providers.llm.base import LLMProvider, LLMResponseValidationError
from app.schemas.qc import QCReport
from app.schemas.showrunner import (
    ShowrunnerQCResponse,
    ShowrunnerResponse,
    ShowrunnerState,
)
from app.schemas.showrunner import WriterBrief, WriterBriefResponse
from app.services.character_service import (
    CharacterBiblesNotFoundError,
    load_character_bibles,
)
from app.services.memory_service import load_story_memory
from app.services.outline_service import ProjectNotFoundError, load_outline
from app.services.project_service import get_project


class ShowrunnerStateNotFoundError(Exception):
    """Project does not have a generated Showrunner State."""


class ShowrunnerEpisodeNotFoundError(Exception):
    """Requested episode is not present in the Showrunner episode plan."""


class WriterBriefNotFoundError(Exception):
    """Requested episode does not have a generated Writer Brief."""


class ShowrunnerQCReportNotFoundError(Exception):
    """Requested episode does not have a persisted Showrunner QC report."""


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


def _brief_response(
    project: Project,
    episode_number: int,
    brief: WriterBrief,
) -> WriterBriefResponse:
    return WriterBriefResponse(
        project_id=project.id,
        episode_number=episode_number,
        brief=brief,
    )


def _qc_response(
    project: Project,
    episode_number: int,
    report: QCReport,
) -> ShowrunnerQCResponse:
    return ShowrunnerQCResponse(
        project_id=project.id,
        episode_number=episode_number,
        report=report,
    )


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

    log_event(
        "workflow.showrunner.started",
        project_id=project_id,
        episode_count=len(outline.episodes),
        character_count=len(characters.characters),
    )
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
    log_event(
        "workflow.showrunner.generated",
        project_id=project.id,
        episode_count=len(state.episode_plan),
        character_arc_count=len(state.character_arcs),
    )
    return _response(project, state)


def get_showrunner_state(db: Session, project_id: int) -> ShowrunnerResponse:
    project = get_project(db, project_id)
    if project is None:
        raise ProjectNotFoundError
    state = load_showrunner_state(project)
    return _response(project, state)


def _ensure_episode_in_plan(state: ShowrunnerState, episode_number: int) -> None:
    if not any(episode.episode_number == episode_number for episode in state.episode_plan):
        raise ShowrunnerEpisodeNotFoundError


def generate_writer_brief(
    db: Session,
    project_id: int,
    episode_number: int,
    target_duration_seconds: int,
    llm_provider: LLMProvider,
) -> WriterBriefResponse:
    project = get_project(db, project_id)
    if project is None:
        raise ProjectNotFoundError
    state = load_showrunner_state(project)
    _ensure_episode_in_plan(state, episode_number)

    story_memory = load_story_memory(project)
    log_event(
        "workflow.writer_brief.started",
        project_id=project_id,
        episode_number=episode_number,
        target_duration_seconds=target_duration_seconds,
    )
    brief = ShowrunnerAgent(llm_provider).generate_writer_brief(
        state=state,
        episode_number=episode_number,
        story_memory=story_memory,
        target_duration_seconds=target_duration_seconds,
    )
    if brief.episode_number != episode_number:
        raise LLMResponseValidationError("Writer brief episode_number mismatch")
    if brief.target_duration_seconds != target_duration_seconds:
        raise LLMResponseValidationError(
            "Writer brief target_duration_seconds mismatch"
        )

    state_data = state.model_dump(mode="json")
    writer_briefs = dict(state_data.get("writer_briefs") or {})
    writer_briefs[str(episode_number)] = brief.model_dump(mode="json")
    state_data["writer_briefs"] = writer_briefs
    state = ShowrunnerState.model_validate(state_data)

    project.showrunner_json = state.model_dump_json()
    db.commit()
    db.refresh(project)
    log_event(
        "workflow.writer_brief.generated",
        project_id=project.id,
        episode_number=episode_number,
        target_duration_seconds=brief.target_duration_seconds,
    )
    return _brief_response(project, episode_number, brief)


def get_writer_brief(
    db: Session,
    project_id: int,
    episode_number: int,
) -> WriterBriefResponse:
    project = get_project(db, project_id)
    if project is None:
        raise ProjectNotFoundError
    state = load_showrunner_state(project)
    _ensure_episode_in_plan(state, episode_number)

    stored = state.writer_briefs.get(str(episode_number))
    if stored is None:
        raise WriterBriefNotFoundError
    brief = WriterBrief.model_validate(stored)
    return _brief_response(project, episode_number, brief)


def save_showrunner_qc_report(
    project: Project,
    episode_number: int,
    report: QCReport,
) -> ShowrunnerState:
    state = load_showrunner_state(project)
    _ensure_episode_in_plan(state, episode_number)
    if report.episode_number != episode_number:
        raise LLMResponseValidationError("Showrunner QC episode_number mismatch")

    state_data = state.model_dump(mode="json")
    qc_reports = dict(state_data.get("qc_reports") or {})
    qc_reports[str(episode_number)] = report.model_dump(mode="json")
    state_data["qc_reports"] = qc_reports
    state = ShowrunnerState.model_validate(state_data)
    project.showrunner_json = state.model_dump_json()
    log_event(
        "workflow.showrunner_qc.saved",
        project_id=project.id,
        episode_number=episode_number,
        qc_status=report.status,
        issue_count=len(report.issues),
    )
    return state


def get_showrunner_qc_report(
    db: Session,
    project_id: int,
    episode_number: int,
) -> ShowrunnerQCResponse:
    project = get_project(db, project_id)
    if project is None:
        raise ProjectNotFoundError
    state = load_showrunner_state(project)
    _ensure_episode_in_plan(state, episode_number)

    stored = state.qc_reports.get(str(episode_number))
    if stored is None:
        raise ShowrunnerQCReportNotFoundError
    report = QCReport.model_validate(
        stored,
        context={"expected_episode_number": episode_number},
    )
    return _qc_response(project, episode_number, report)
