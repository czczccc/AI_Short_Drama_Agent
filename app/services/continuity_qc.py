from app.schemas.qc import QCIssue, QCReport
from app.schemas.script import EpisodeScript


def _recommended_scene_limit(target_duration_seconds: int) -> int:
    return min(8, max(3, target_duration_seconds // 18))


def evaluate_script_rules(
    script: EpisodeScript,
    target_duration_seconds: int,
) -> list[QCIssue]:
    issues: list[QCIssue] = []
    scene_limit = _recommended_scene_limit(target_duration_seconds)
    if len(script.scenes) > scene_limit:
        issues.append(
            QCIssue(
                episode_number=script.episode_number,
                severity="warning",
                code="episode_overloaded",
                message=(
                    f"{target_duration_seconds}秒目标时长包含"
                    f"{len(script.scenes)}个场景，超过建议上限{scene_limit}个。"
                ),
                suggestion="合并功能重复的场景，保留核心冲突和结尾钩子。",
            )
        )

    for scene in script.scenes:
        missing_character_ids = sorted(
            {
                dialogue.character_id
                for dialogue in scene.dialogues
                if dialogue.character_id not in scene.characters
            }
        )
        if missing_character_ids:
            issues.append(
                QCIssue(
                    episode_number=script.episode_number,
                    severity="error",
                    code="scene_character_mismatch",
                    message=(
                        f"第{scene.scene_number}场对白角色未列入场景角色："
                        f"{', '.join(missing_character_ids)}。"
                    ),
                    suggestion="把实际说话角色加入该场 characters，或删除错误对白。",
                )
            )
    return issues


def merge_qc_report(
    report: QCReport,
    rule_issues: list[QCIssue],
) -> QCReport:
    if not rule_issues:
        return report

    issues = list(rule_issues)
    seen = {(issue.code, issue.message) for issue in issues}
    issues.extend(
        issue
        for issue in report.issues
        if (issue.code, issue.message) not in seen
    )
    if any(issue.severity == "error" for issue in issues):
        status = "fail"
    elif issues:
        status = "warning"
    else:
        status = report.status

    summary = report.summary
    if status != report.status:
        summary = "规则型 QC 发现需要修改的问题；" + summary
    return QCReport.model_validate(
        {
            **report.model_dump(mode="json"),
            "status": status,
            "summary": summary,
            "issues": [issue.model_dump(mode="json") for issue in issues],
            "approved_memory": (
                report.approved_memory.model_dump(mode="json")
                if status == "pass" and report.approved_memory is not None
                else None
            ),
        }
    )
