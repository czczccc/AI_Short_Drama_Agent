from app.schemas.memory import EpisodeMemory, StoryMemory
from app.services.showrunner_service import build_continuity_contract


def test_build_continuity_contract_uses_previous_approved_ending_and_obligations() -> None:
    previous = EpisodeMemory.model_validate(
        {
            "episode_number": 1,
            "source": "qc_approved",
            "summary": "林峰复制文件后看见异常名字。",
            "unresolved_questions": ["异常名字为什么出现。"],
            "ending_state": {
                "location": "人工智能公司机房",
                "time_of_day": "深夜",
                "situation": "林峰看见屏幕上的异常名字。",
            },
            "ending_hook": "异常名字为什么出现。",
            "continuity_obligations": [
                {
                    "obligation_id": "e1_trace_the_name",
                    "kind": "active_crisis",
                    "description": "追查屏幕上出现的名字。",
                    "source_episode_number": 1,
                    "due_episode_number": 2,
                    "source_memory_path": "unresolved_questions.0",
                }
            ],
        }
    )
    memory = StoryMemory(episodes={"1": previous})

    contract = build_continuity_contract(memory, episode_number=2)

    assert contract is not None
    assert contract.previous_episode_number == 1
    assert contract.previous_ending_state == previous.ending_state
    assert [item.obligation_id for item in contract.must_continue] == [
        "episode_1_ending_state",
        "e1_trace_the_name",
    ]
    assert contract.must_continue[0].kind == "ending_state"
    assert contract.must_continue[0].due_episode_number == 2


def test_build_continuity_contract_is_empty_without_previous_official_memory() -> None:
    contract = build_continuity_contract(StoryMemory(), episode_number=2)

    assert contract is None


def test_build_continuity_contract_ignores_rule_extracted_memory() -> None:
    previous = EpisodeMemory.model_validate(
        {
            "episode_number": 1,
            "source": "rule_extracted",
            "summary": "规则摘要不具备 QC 场景证据。",
            "ending_state": {
                "location": "人工智能公司机房",
                "time_of_day": "深夜",
                "situation": "该处境未经 QC 证据确认。",
            },
            "ending_hook": "未经确认的悬念。",
        }
    )

    contract = build_continuity_contract(
        StoryMemory(episodes={"1": previous}),
        episode_number=2,
    )

    assert contract is None
