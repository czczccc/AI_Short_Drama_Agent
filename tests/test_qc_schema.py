import pytest
from pydantic import ValidationError

from app.schemas.qc import ContinuityResolution, QCIssue, QCReport
from tests.fakes import (
    valid_qc_fail_report_data,
    valid_qc_pass_report_data,
    valid_qc_report_data,
)


def test_qc_pass_requires_approved_memory_in_generation_context() -> None:
    data = valid_qc_pass_report_data()
    data["approved_memory"] = None

    with pytest.raises(ValidationError):
        QCReport.model_validate(
            data,
            context={
                "expected_episode_number": 1,
                "require_approved_memory": True,
            },
        )


def test_qc_pass_approved_memory_matches_episode() -> None:
    data = valid_qc_pass_report_data()
    data["approved_memory"]["episode_number"] = 2

    with pytest.raises(ValidationError):
        QCReport.model_validate(
            data,
            context={
                "expected_episode_number": 1,
                "require_approved_memory": True,
            },
        )


def test_qc_pass_approved_memory_must_be_qc_approved() -> None:
    data = valid_qc_pass_report_data()
    data["approved_memory"]["source"] = "rule_extracted"

    with pytest.raises(ValidationError):
        QCReport.model_validate(
            data,
            context={
                "expected_episode_number": 1,
                "require_approved_memory": True,
            },
        )


def test_qc_pass_approved_memory_requires_ending_state() -> None:
    data = valid_qc_pass_report_data()
    data["approved_memory"]["ending_state"] = None

    with pytest.raises(ValidationError):
        QCReport.model_validate(
            data,
            context={
                "expected_episode_number": 1,
                "require_approved_memory": True,
            },
        )


def test_qc_warning_cannot_publish_approved_memory() -> None:
    data = valid_qc_report_data()
    data["approved_memory"] = valid_qc_pass_report_data()["approved_memory"]

    with pytest.raises(ValidationError):
        QCReport.model_validate(data)


def test_qc_status_cannot_pass_with_warning_issue() -> None:
    data = valid_qc_report_data()
    data["status"] = "pass"

    with pytest.raises(ValidationError):
        QCReport.model_validate(data)


def test_qc_error_issue_requires_fail_status() -> None:
    data = valid_qc_fail_report_data()
    data["status"] = "warning"

    with pytest.raises(ValidationError):
        QCReport.model_validate(data)


def test_qc_warning_requires_at_least_one_issue() -> None:
    data = valid_qc_pass_report_data()
    data["status"] = "warning"
    data["approved_memory"] = None

    with pytest.raises(ValidationError):
        QCReport.model_validate(data)


def test_unknown_legacy_qc_issue_code_normalizes_to_other() -> None:
    issue = QCIssue.model_validate(
        {
            "episode_number": 1,
            "severity": "warning",
            "code": "legacy_free_form_code",
            "message": "旧报告使用了自由格式问题码。",
            "suggestion": None,
        }
    )

    assert issue.code == "other"


@pytest.mark.parametrize(
    ("status_fields", "expected_status"),
    [
        ({"resolved": True}, "resolved"),
        ({"carried_to_next_episode": True}, "carried_forward"),
        ({"carries_forward": True}, "carried_forward"),
    ],
)
def test_continuity_resolution_normalizes_observed_status_aliases(
    status_fields: dict[str, bool],
    expected_status: str,
) -> None:
    resolution = ContinuityResolution.model_validate(
        {
            "obligation_id": "episode_1_ending_state",
            "scene_number": 1,
            "resolution_evidence": "屏幕上的名字仍在闪烁。",
            "kind": "ending_state",
            "resolution_notes": "第一场已承接。",
            **status_fields,
        }
    )

    assert resolution.model_dump() == {
        "obligation_id": "episode_1_ending_state",
        "status": expected_status,
        "scene_number": 1,
        "evidence_text": "屏幕上的名字仍在闪烁。",
    }


def test_continuity_resolution_normalizes_evidence_alias() -> None:
    resolution = ContinuityResolution.model_validate(
        {
            "obligation_id": "episode_1_ending_state",
            "status": "resolved",
            "scene_number": 1,
            "evidence": "林峰仍站在机房屏幕前。",
        }
    )

    assert resolution.evidence_text == "林峰仍站在机房屏幕前。"


@pytest.mark.parametrize(
    "data",
    [
        {
            "obligation_id": "episode_1_ending_state",
            "status": "resolved",
            "scene_number": 1,
            "evidence_text": "证据甲。",
            "evidence": "证据乙。",
        },
        {
            "obligation_id": "episode_1_ending_state",
            "status": "resolved",
            "scene_number": 1,
            "evidence_text": "屏幕上的名字仍在闪烁。",
            "carried_to_next_episode": True,
        },
        {
            "obligation_id": "episode_1_ending_state",
            "scene_number": 1,
            "evidence_text": "屏幕上的名字仍在闪烁。",
            "resolved": True,
            "carries_forward": True,
        },
    ],
)
def test_continuity_resolution_rejects_conflicting_aliases(
    data: dict[str, object],
) -> None:
    with pytest.raises(ValidationError):
        ContinuityResolution.model_validate(data)


def test_continuity_resolution_does_not_infer_missing_scene_number() -> None:
    with pytest.raises(ValidationError):
        ContinuityResolution.model_validate(
            {
                "obligation_id": "episode_1_ending_state",
                "resolved": True,
                "resolution_evidence": "屏幕上的名字仍在闪烁。",
            }
        )


def test_continuity_resolution_still_rejects_unknown_extra_fields() -> None:
    with pytest.raises(ValidationError):
        ContinuityResolution.model_validate(
            {
                "obligation_id": "episode_1_ending_state",
                "status": "resolved",
                "scene_number": 1,
                "evidence_text": "屏幕上的名字仍在闪烁。",
                "unexpected": "不能静默丢弃。",
            }
        )


def test_qc_report_still_rejects_relationship_change_objects() -> None:
    data = valid_qc_pass_report_data()
    data["approved_memory"]["character_updates"]["lin_feng"][
        "relationship_changes"
    ] = [{"target": "wang_ze", "change": "开始怀疑"}]

    with pytest.raises(ValidationError):
        QCReport.model_validate(data)
