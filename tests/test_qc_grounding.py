import pytest

from app.schemas.qc import QCReport
from app.schemas.script import EpisodeScript
from app.schemas.showrunner import WriterBrief
from app.services.qc_grounding import (
    QCReportGroundingError,
    build_scene_evidence_catalog,
    complete_missing_continuity_obligations,
    normalize_surplus_memory_evidence,
    validate_qc_report_grounding,
)
from tests.fakes import (
    valid_qc_pass_report_data,
    valid_script_data,
    valid_writer_brief_data,
)


def _grounded_pass_report(episode_number: int = 1) -> QCReport:
    data = valid_qc_pass_report_data(episode_number)
    data["approved_memory"]["continuity_obligations"] = [
        {
            "obligation_id": f"e{episode_number}_trace_the_name",
            "kind": "active_crisis",
            "description": "追查屏幕上出现的名字。",
            "source_episode_number": episode_number,
            "due_episode_number": episode_number + 1,
            "source_memory_path": "unresolved_questions.0",
        }
    ]
    data["memory_evidence"] = [
        {
            "memory_path": "summary",
            "scene_number": 3,
            "evidence_text": "林峰迅速复制关键文件",
        },
        {
            "memory_path": "new_facts.0",
            "scene_number": 3,
            "evidence_text": "林峰迅速复制关键文件",
        },
        {
            "memory_path": "unresolved_questions.0",
            "scene_number": 3,
            "evidence_text": "屏幕上出现苏妍父亲的名字",
        },
        {
            "memory_path": "character_updates.lin_feng.knows.0",
            "scene_number": 3,
            "evidence_text": "林峰迅速复制关键文件",
        },
        {
            "memory_path": "character_updates.lin_feng.current_goal",
            "scene_number": 3,
            "evidence_text": "屏幕上出现苏妍父亲的名字",
        },
        {
            "memory_path": "props_and_evidence.0",
            "scene_number": 3,
            "evidence_text": "林峰迅速复制关键文件",
        },
        {
            "memory_path": "ending_state",
            "scene_number": 3,
            "evidence_text": "屏幕上出现苏妍父亲的名字",
        },
        {
            "memory_path": "ending_hook",
            "scene_number": 3,
            "evidence_text": "屏幕上出现苏妍父亲的名字",
        },
        {
            "memory_path": "continuity_obligations.0",
            "scene_number": 3,
            "evidence_text": "屏幕上出现苏妍父亲的名字",
        },
    ]
    data["continuity_resolutions"] = []
    return QCReport.model_validate(data)


def test_scene_evidence_catalog_contains_only_groundable_script_text() -> None:
    script = EpisodeScript.model_validate(valid_script_data())

    catalog = build_scene_evidence_catalog(script)

    assert {
        "scene_number": 1,
        "evidence_text": "电脑突然开始远程自毁，警报声逼近，林峰迅速复制关键文件。",
    } in catalog
    assert {
        "scene_number": 1,
        "evidence_text": "只剩十秒，必须拿到证据！",
    } in catalog
    assert {
        "scene_number": 1,
        "evidence_text": "手指飞快敲击键盘。",
    } in catalog
    assert not any(
        item["evidence_text"] == script.scenes[0].scene_goal
        for item in catalog
    )
    assert not any(
        item["evidence_text"] == script.opening_hook
        for item in catalog
    )


def test_grounded_qc_pass_accepts_scene_backed_memory() -> None:
    report = _grounded_pass_report()
    script = EpisodeScript.model_validate(valid_script_data())

    validate_qc_report_grounding(report, script)


def test_complete_missing_continuity_obligations_reuses_unresolved_question_evidence_verbatim() -> None:
    data = valid_qc_pass_report_data(episode_number=1)
    data["approved_memory"]["continuity_obligations"] = []
    data["memory_evidence"] = [
        evidence
        for evidence in data["memory_evidence"]
        if evidence["memory_path"] != "continuity_obligations.0"
    ]
    report = QCReport.model_validate(data)
    unresolved_evidence = next(
        evidence
        for evidence in report.memory_evidence
        if evidence.memory_path == "unresolved_questions.0"
    )

    normalized = complete_missing_continuity_obligations(report)

    assert normalized is not report
    assert normalized.approved_memory is not None
    assert len(normalized.approved_memory.continuity_obligations) == 1
    obligation = normalized.approved_memory.continuity_obligations[0]
    assert obligation.source_memory_path == "unresolved_questions.0"
    new_evidence = next(
        evidence
        for evidence in normalized.memory_evidence
        if evidence.memory_path == "continuity_obligations.0"
    )
    assert new_evidence.scene_number == unresolved_evidence.scene_number
    assert new_evidence.evidence_text == unresolved_evidence.evidence_text


def test_complete_missing_continuity_obligations_preserves_existing_obligations_and_is_idempotent() -> None:
    data = valid_qc_pass_report_data(episode_number=1)
    report = QCReport.model_validate(data)
    original_obligation = data["approved_memory"]["continuity_obligations"][0]
    original_evidence = next(
        evidence
        for evidence in report.memory_evidence
        if evidence.memory_path == "continuity_obligations.0"
    )

    normalized = complete_missing_continuity_obligations(report)

    assert normalized is not report
    assert normalized.approved_memory is not None
    assert len(normalized.approved_memory.continuity_obligations) == 1
    obligation = normalized.approved_memory.continuity_obligations[0]
    assert obligation.obligation_id == original_obligation["obligation_id"]
    assert obligation.kind == original_obligation["kind"]
    assert obligation.description == original_obligation["description"]
    assert (
        obligation.source_memory_path
        == original_obligation["source_memory_path"]
    )
    assert len(normalized.memory_evidence) == len(report.memory_evidence)
    assert next(
        evidence
        for evidence in normalized.memory_evidence
        if evidence.memory_path == "continuity_obligations.0"
    ).model_dump(mode="json") == original_evidence.model_dump(mode="json")

    again = complete_missing_continuity_obligations(normalized)
    assert again.model_dump(mode="json") == normalized.model_dump(mode="json")


def test_complete_missing_continuity_obligations_skips_episode_10() -> None:
    data = valid_qc_pass_report_data(episode_number=10)
    assert data["approved_memory"]["continuity_obligations"] == []
    report = QCReport.model_validate(data)
    assert report.approved_memory is not None
    assert len(report.approved_memory.unresolved_questions) >= 1

    normalized = complete_missing_continuity_obligations(report)

    assert normalized.approved_memory is not None
    assert normalized.approved_memory.continuity_obligations == []
    assert not any(
        evidence.memory_path.startswith("continuity_obligations.")
        for evidence in normalized.memory_evidence
    )


def test_surplus_memory_evidence_normalization_only_removes_safe_extras() -> None:
    report = _grounded_pass_report()
    original = report.memory_evidence[0]
    report.memory_evidence.extend(
        [
            original.model_copy(deep=True),
            original.model_copy(
                update={"memory_path": "character_updates.unknown.knows.0"},
                deep=True,
            ),
        ]
    )

    normalized = normalize_surplus_memory_evidence(report)

    assert normalized is not report
    assert len(normalized.memory_evidence) == len(report.memory_evidence) - 2
    assert normalized.memory_evidence.count(original) == 1


def test_grounded_qc_pass_rejects_nonexistent_evidence_text() -> None:
    report = _grounded_pass_report()
    report.memory_evidence[0].evidence_text = "场景里从未出现的事实"
    script = EpisodeScript.model_validate(valid_script_data())

    with pytest.raises(QCReportGroundingError) as exc_info:
        validate_qc_report_grounding(report, script)

    assert "evidence_text_not_found" in exc_info.value.reason_codes


def test_grounded_qc_pass_rejects_missing_memory_path_coverage() -> None:
    report = _grounded_pass_report()
    report.memory_evidence = [
        evidence
        for evidence in report.memory_evidence
        if evidence.memory_path != "new_facts.0"
    ]
    script = EpisodeScript.model_validate(valid_script_data())

    with pytest.raises(QCReportGroundingError) as exc_info:
        validate_qc_report_grounding(report, script)

    assert "missing_memory_evidence" in exc_info.value.reason_codes


def test_grounded_qc_pass_rejects_ending_state_not_matching_final_scene() -> None:
    report = _grounded_pass_report()
    assert report.approved_memory is not None
    assert report.approved_memory.ending_state is not None
    report.approved_memory.ending_state.location = "不存在的地点"
    script = EpisodeScript.model_validate(valid_script_data())

    with pytest.raises(QCReportGroundingError) as exc_info:
        validate_qc_report_grounding(report, script)

    assert "ending_state_mismatch" in exc_info.value.reason_codes


def test_grounded_qc_pass_requires_resolution_for_every_contract_item() -> None:
    report = _grounded_pass_report(episode_number=2)
    script = EpisodeScript.model_validate(valid_script_data(episode_number=2))
    brief_data = valid_writer_brief_data(episode_number=2)
    brief_data["continuity_contract"] = {
        "previous_episode_number": 1,
        "previous_ending_state": {
            "location": "人工智能公司机房",
            "time_of_day": "深夜",
            "situation": "林峰看见屏幕上的异常名字。",
        },
        "must_continue": [
            {
                "obligation_id": "episode_1_ending_state",
                "kind": "ending_state",
                "description": "承接上一集的结尾处境。",
                "source_episode_number": 1,
                "due_episode_number": 2,
                "source_memory_path": "ending_state",
            }
        ],
    }
    brief = WriterBrief.model_validate(brief_data)

    with pytest.raises(QCReportGroundingError) as exc_info:
        validate_qc_report_grounding(report, script, brief)

    assert "missing_continuity_resolution" in exc_info.value.reason_codes


def test_normalize_carried_obligation_sources_restores_contract_origin() -> None:
    """写回义务的 source_episode_number 应从合同恢复原始来源集，而非模型填的当前集。"""
    from app.services.qc_grounding import normalize_carried_obligation_sources

    report = _grounded_pass_report(episode_number=5)
    report.approved_memory.continuity_obligations[0].source_episode_number = 5
    report.approved_memory.continuity_obligations[0].obligation_id = "e1_find_phone"

    brief_data = valid_writer_brief_data(episode_number=5)
    brief_data["continuity_contract"] = {
        "previous_episode_number": 4,
        "previous_ending_state": {
            "location": "废弃仓库",
            "time_of_day": "凌晨",
            "situation": "两人发现加密信息。",
        },
        "must_continue": [
            {
                "obligation_id": "e1_find_phone",
                "kind": "active_crisis",
                "description": "找回丢失的手机。",
                "source_episode_number": 1,
                "due_episode_number": 5,
                "source_memory_path": "unresolved_questions.0",
            }
        ],
    }
    brief = WriterBrief.model_validate(brief_data)

    normalized = normalize_carried_obligation_sources(report, brief)

    obligation = normalized.approved_memory.continuity_obligations[0]
    assert obligation.source_episode_number == 1
    assert obligation.obligation_id == "e1_find_phone"


def test_grounded_qc_pass_rejects_overdue_carried_forward() -> None:
    """来源超过 2 集的义务若仍标 carried_forward 必须报 overdue_obligation_must_resolve。"""
    report = _grounded_pass_report(episode_number=5)
    report.approved_memory.continuity_obligations[0].source_episode_number = 1
    report.approved_memory.continuity_obligations[0].obligation_id = "e1_find_phone"
    from app.schemas.qc import ContinuityResolution

    report.continuity_resolutions = [
        ContinuityResolution.model_validate(
            {
                "obligation_id": "e1_find_phone",
                "status": "carried_forward",
                "scene_number": 3,
                "evidence_text": "屏幕上出现苏妍父亲的名字",
            }
        )
    ]

    script = EpisodeScript.model_validate(valid_script_data(episode_number=5))
    brief_data = valid_writer_brief_data(episode_number=5)
    brief_data["continuity_contract"] = {
        "previous_episode_number": 4,
        "previous_ending_state": {
            "location": "废弃仓库",
            "time_of_day": "凌晨",
            "situation": "两人发现加密信息。",
        },
        "must_continue": [
            {
                "obligation_id": "e1_find_phone",
                "kind": "active_crisis",
                "description": "找回丢失的手机。",
                "source_episode_number": 1,
                "due_episode_number": 5,
                "source_memory_path": "unresolved_questions.0",
            }
        ],
    }
    brief = WriterBrief.model_validate(brief_data)

    with pytest.raises(QCReportGroundingError) as exc_info:
        validate_qc_report_grounding(report, script, brief)

    assert "overdue_obligation_must_resolve" in exc_info.value.reason_codes
