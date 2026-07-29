from app.schemas.showrunner import ShowrunnerState, WriterBrief
from tests.fakes import valid_showrunner_state_data, valid_writer_brief_data


def test_showrunner_state_requires_empty_future_phase_fields() -> None:
    state = ShowrunnerState.model_validate(valid_showrunner_state_data())

    assert state.version == "showrunner_v1"
    assert state.writer_briefs == {}
    assert state.qc_reports == {}
    assert state.story_bible.series_title == "逆光代码"
    assert len(state.episode_plan) == 10
    assert len(state.character_arcs) == 3


def test_writer_brief_validates_episode_number_and_scope_fields() -> None:
    brief = WriterBrief.model_validate(valid_writer_brief_data(episode_number=2))

    assert brief.episode_number == 2
    assert brief.target_duration_seconds == 90
    assert brief.allowed_scope
    assert brief.forbidden_content
    assert brief.character_states[0].character_id == "lin_feng"
