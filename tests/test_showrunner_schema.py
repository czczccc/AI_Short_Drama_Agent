from app.schemas.showrunner import ShowrunnerState
from tests.fakes import valid_showrunner_state_data


def test_showrunner_state_requires_empty_future_phase_fields() -> None:
    state = ShowrunnerState.model_validate(valid_showrunner_state_data())

    assert state.version == "showrunner_v1"
    assert state.writer_briefs == {}
    assert state.qc_reports == {}
    assert state.story_bible.series_title == "逆光代码"
    assert len(state.episode_plan) == 10
    assert len(state.character_arcs) == 3

