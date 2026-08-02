from app.schemas.memory import ContinuityObligation
from app.schemas.qc import MemoryEvidence, QCReport
from app.schemas.script import EpisodeScript, SceneScript
from app.schemas.showrunner import WriterBrief


class QCReportGroundingError(ValueError):
    def __init__(self, issues: list[dict]) -> None:
        super().__init__("QC report grounding validation failed")
        self.issues = issues
        self.reason_codes = sorted({issue["type"] for issue in issues})


def _scene_evidence_fragments(scene: SceneScript) -> list[str]:
    fragments = [
        scene.action,
        scene.transition,
    ]
    for dialogue in scene.dialogues:
        fragments.extend(
            [
                dialogue.line,
                dialogue.action_note,
            ]
        )
    return [fragment.strip() for fragment in fragments if fragment]


def build_scene_evidence_catalog(
    script: EpisodeScript,
) -> list[dict[str, int | str]]:
    catalog: list[dict[str, int | str]] = []
    seen: set[tuple[int, str]] = set()
    for scene in script.scenes:
        for evidence_text in _scene_evidence_fragments(scene):
            key = (scene.scene_number, evidence_text)
            if key in seen:
                continue
            seen.add(key)
            catalog.append(
                {
                    "scene_number": scene.scene_number,
                    "evidence_text": evidence_text,
                }
            )
    return catalog


def _evidence_exists(
    script: EpisodeScript,
    scene_number: int,
    evidence_text: str,
) -> bool:
    scene = next(
        (
            item
            for item in script.scenes
            if item.scene_number == scene_number
        ),
        None,
    )
    if scene is None:
        return False
    text = evidence_text.strip()
    return any(text in fragment for fragment in _scene_evidence_fragments(scene))


def _required_memory_paths(report: QCReport) -> set[str]:
    memory = report.approved_memory
    if memory is None:
        return set()

    paths = {"summary", "ending_hook"}
    paths.update(f"new_facts.{index}" for index, _ in enumerate(memory.new_facts))
    paths.update(
        f"revealed_secrets.{index}"
        for index, _ in enumerate(memory.revealed_secrets)
    )
    paths.update(
        f"unresolved_questions.{index}"
        for index, _ in enumerate(memory.unresolved_questions)
    )
    for character_id, update in memory.character_updates.items():
        paths.update(
            f"character_updates.{character_id}.knows.{index}"
            for index, _ in enumerate(update.knows)
        )
        if update.current_goal is not None:
            paths.add(f"character_updates.{character_id}.current_goal")
        paths.update(
            f"character_updates.{character_id}.relationship_changes.{index}"
            for index, _ in enumerate(update.relationship_changes)
        )
    paths.update(
        f"props_and_evidence.{index}"
        for index, _ in enumerate(memory.props_and_evidence)
    )
    if memory.ending_state is not None:
        paths.add("ending_state")
    paths.update(
        f"continuity_obligations.{index}"
        for index, _ in enumerate(memory.continuity_obligations)
    )
    return paths


def complete_missing_continuity_obligations(report: QCReport) -> QCReport:
    memory = report.approved_memory
    if report.status != "pass" or memory is None or memory.episode_number >= 10:
        return report

    normalized = report.model_copy(deep=True)
    normalized_memory = normalized.approved_memory
    if normalized_memory is None:
        return normalized

    existing_source_paths = {
        item.source_memory_path
        for item in normalized_memory.continuity_obligations
    }
    evidence_by_path = {
        item.memory_path: item
        for item in normalized.memory_evidence
    }
    for index, question in enumerate(normalized_memory.unresolved_questions):
        source_path = f"unresolved_questions.{index}"
        if source_path in existing_source_paths:
            continue

        obligation_index = len(normalized_memory.continuity_obligations)
        normalized_memory.continuity_obligations.append(
            ContinuityObligation(
                obligation_id=(
                    f"e{normalized_memory.episode_number}_unresolved_question_"
                    f"{index + 1}"
                ),
                kind="active_crisis",
                description=question,
                source_episode_number=normalized_memory.episode_number,
                due_episode_number=normalized_memory.episode_number + 1,
                source_memory_path=source_path,
            )
        )
        source_evidence = evidence_by_path.get(source_path)
        if source_evidence is not None:
            normalized.memory_evidence.append(
                MemoryEvidence(
                    memory_path=f"continuity_obligations.{obligation_index}",
                    scene_number=source_evidence.scene_number,
                    evidence_text=source_evidence.evidence_text,
                )
            )
        existing_source_paths.add(source_path)
    return normalized


def normalize_surplus_memory_evidence(report: QCReport) -> QCReport:
    if report.status != "pass" or report.approved_memory is None:
        return report

    required_paths = _required_memory_paths(report)
    normalized = report.model_copy(deep=True)
    seen: set[tuple[str, int, str]] = set()
    normalized_evidence = []
    for evidence in normalized.memory_evidence:
        identity = (
            evidence.memory_path,
            evidence.scene_number,
            evidence.evidence_text,
        )
        if evidence.memory_path not in required_paths or identity in seen:
            continue
        seen.add(identity)
        normalized_evidence.append(evidence)
    normalized.memory_evidence = normalized_evidence
    return normalized


def _validate_memory_evidence(
    report: QCReport,
    script: EpisodeScript,
) -> list[dict]:
    required_paths = _required_memory_paths(report)
    evidence_paths = [item.memory_path for item in report.memory_evidence]
    evidence_path_set = set(evidence_paths)
    issues: list[dict] = []

    missing_paths = sorted(required_paths - evidence_path_set)
    if missing_paths:
        issues.append(
            {
                "type": "missing_memory_evidence",
                "memory_paths": missing_paths,
            }
        )
    unexpected_paths = sorted(evidence_path_set - required_paths)
    if unexpected_paths:
        issues.append(
            {
                "type": "unknown_memory_evidence_path",
                "memory_paths": unexpected_paths,
            }
        )
    duplicate_paths = sorted(
        {
            path
            for path in evidence_paths
            if evidence_paths.count(path) > 1
        }
    )
    if duplicate_paths:
        issues.append(
            {
                "type": "duplicate_memory_evidence",
                "memory_paths": duplicate_paths,
            }
        )

    for evidence in report.memory_evidence:
        if not _evidence_exists(
            script,
            evidence.scene_number,
            evidence.evidence_text,
        ):
            issues.append(
                {
                    "type": "evidence_text_not_found",
                    "memory_path": evidence.memory_path,
                    "scene_number": evidence.scene_number,
                }
            )
    return issues


def _validate_ending_state(
    report: QCReport,
    script: EpisodeScript,
) -> list[dict]:
    memory = report.approved_memory
    if memory is None or memory.ending_state is None:
        return []
    final_scene = script.scenes[-1]
    if (
        memory.ending_state.location == final_scene.location
        and memory.ending_state.time_of_day == final_scene.time_of_day
    ):
        return []
    return [
        {
            "type": "ending_state_mismatch",
            "expected_scene_number": final_scene.scene_number,
        }
    ]


def _validate_new_obligations(report: QCReport, script: EpisodeScript) -> list[dict]:
    memory = report.approved_memory
    if memory is None:
        return []
    issues: list[dict] = []
    obligation_ids = [
        item.obligation_id for item in memory.continuity_obligations
    ]
    duplicate_ids = sorted(
        {
            obligation_id
            for obligation_id in obligation_ids
            if obligation_ids.count(obligation_id) > 1
        }
    )
    if duplicate_ids:
        issues.append(
            {
                "type": "duplicate_continuity_obligation",
                "obligation_ids": duplicate_ids,
            }
        )

    unresolved_paths = {
        f"unresolved_questions.{index}"
        for index, _ in enumerate(memory.unresolved_questions)
    }
    allowed_source_paths = {
        path
        for path in _required_memory_paths(report)
        if path not in {"summary", "ending_state"}
        and not path.startswith("continuity_obligations.")
    }
    obligation_source_paths = {
        item.source_memory_path for item in memory.continuity_obligations
    }
    if script.episode_number < 10:
        missing_obligations = sorted(unresolved_paths - obligation_source_paths)
        if missing_obligations:
            issues.append(
                {
                    "type": "unresolved_question_without_obligation",
                    "memory_paths": missing_obligations,
                }
            )
    for obligation in memory.continuity_obligations:
        if (
            obligation.source_episode_number != script.episode_number
            or obligation.due_episode_number != script.episode_number + 1
        ):
            issues.append(
                {
                    "type": "invalid_continuity_obligation_episode",
                    "obligation_id": obligation.obligation_id,
                }
            )
        if obligation.source_memory_path not in allowed_source_paths:
            issues.append(
                {
                    "type": "invalid_continuity_obligation_source",
                    "obligation_id": obligation.obligation_id,
                }
            )
    return issues


def _validate_continuity_resolutions(
    report: QCReport,
    script: EpisodeScript,
    writer_brief: WriterBrief | None,
) -> list[dict]:
    contract = (
        writer_brief.continuity_contract
        if writer_brief is not None
        else None
    )
    obligations = contract.must_continue if contract is not None else []
    expected = {item.obligation_id: item for item in obligations}
    resolutions = {
        item.obligation_id: item for item in report.continuity_resolutions
    }
    issues: list[dict] = []

    resolution_ids = [
        item.obligation_id for item in report.continuity_resolutions
    ]
    duplicate_ids = sorted(
        {
            obligation_id
            for obligation_id in resolution_ids
            if resolution_ids.count(obligation_id) > 1
        }
    )
    if duplicate_ids:
        issues.append(
            {
                "type": "duplicate_continuity_resolution",
                "obligation_ids": duplicate_ids,
            }
        )

    missing_ids = sorted(set(expected) - set(resolutions))
    if missing_ids:
        issues.append(
            {
                "type": "missing_continuity_resolution",
                "obligation_ids": missing_ids,
            }
        )
    unexpected_ids = sorted(set(resolutions) - set(expected))
    if unexpected_ids:
        issues.append(
            {
                "type": "unknown_continuity_resolution",
                "obligation_ids": unexpected_ids,
            }
        )

    memory = report.approved_memory
    carried_ids = (
        {
            item.obligation_id
            for item in memory.continuity_obligations
        }
        if memory is not None
        else set()
    )
    for obligation_id, resolution in resolutions.items():
        obligation = expected.get(obligation_id)
        if obligation is None:
            continue
        if not _evidence_exists(
            script,
            resolution.scene_number,
            resolution.evidence_text,
        ):
            issues.append(
                {
                    "type": "continuity_evidence_text_not_found",
                    "obligation_id": obligation_id,
                    "scene_number": resolution.scene_number,
                }
            )
        if obligation.kind == "ending_state" and resolution.scene_number != 1:
            issues.append(
                {
                    "type": "previous_ending_not_continued_in_opening",
                    "obligation_id": obligation_id,
                }
            )
        if resolution.status == "carried_forward":
            if script.episode_number == 10 or obligation_id not in carried_ids:
                issues.append(
                    {
                        "type": "carried_forward_obligation_not_saved",
                        "obligation_id": obligation_id,
                    }
                )
        elif obligation_id in carried_ids:
            issues.append(
                {
                    "type": "resolved_obligation_still_active",
                    "obligation_id": obligation_id,
                }
            )
    return issues


def validate_qc_report_grounding(
    report: QCReport,
    script: EpisodeScript,
    writer_brief: WriterBrief | None = None,
) -> None:
    if report.status != "pass":
        return

    issues = [
        *_validate_memory_evidence(report, script),
        *_validate_ending_state(report, script),
        *_validate_new_obligations(report, script),
        *_validate_continuity_resolutions(report, script, writer_brief),
    ]
    if issues:
        raise QCReportGroundingError(issues)
