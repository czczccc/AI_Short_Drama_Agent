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


def test_showrunner_state_accepts_sparse_character_arc_turning_points() -> None:
    data = valid_showrunner_state_data()
    for arc in data["character_arcs"]:
        arc["episode_beats"] = [
            arc["episode_beats"][0],
            arc["episode_beats"][4],
            arc["episode_beats"][9],
        ]

    state = ShowrunnerState.model_validate(data)

    assert [
        beat.episode_number for beat in state.character_arcs[0].episode_beats
    ] == [1, 5, 10]


def test_showrunner_state_allows_empty_final_episode_future_reveals() -> None:
    data = valid_showrunner_state_data()
    data["episode_plan"][9]["must_not_reveal"] = []

    state = ShowrunnerState.model_validate(data)

    assert state.episode_plan[9].must_not_reveal == []


def test_writer_brief_validates_episode_number_and_scope_fields() -> None:
    brief = WriterBrief.model_validate(valid_writer_brief_data(episode_number=2))

    assert brief.episode_number == 2
    assert brief.target_duration_seconds == 90
    assert brief.allowed_scope
    assert brief.forbidden_content
    assert brief.character_states[0].character_id == "lin_feng"


def test_writer_brief_allows_empty_character_knowledge_boundaries() -> None:
    data = valid_writer_brief_data()
    data["character_states"][0]["knows"] = []
    data["character_states"][0]["must_not_know"] = []

    brief = WriterBrief.model_validate(data)

    assert brief.character_states[0].knows == []
    assert brief.character_states[0].must_not_know == []


def test_first_episode_writer_brief_allows_empty_continuity_context() -> None:
    data = valid_writer_brief_data(episode_number=1)
    data["continuity_context"] = []

    brief = WriterBrief.model_validate(data)

    assert brief.continuity_context == []
