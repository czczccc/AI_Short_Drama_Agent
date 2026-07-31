import pytest
from pydantic import ValidationError

from app.schemas.qc import QCIssue, QCReport
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
