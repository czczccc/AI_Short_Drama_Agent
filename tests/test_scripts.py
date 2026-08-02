import json
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.api.main import app
from app.models.project import Project
from app.observability.logging import configure_logging, read_recent_logs
from app.providers.llm.base import LLMCallError
from app.providers.llm.factory import get_configured_llm_provider
from app.schemas.qc import QCReport
from app.schemas.script import EpisodeScript
from tests.fakes import (
    FakeLLMProvider,
    FailingLLMProvider,
    valid_qc_pass_report_data,
    valid_qc_report_data,
    valid_script_data,
)


def create_project(client: TestClient) -> int:
    response = client.post("/projects", json={"name": "剧本测试"})
    assert response.status_code == 201
    return response.json()["id"]


def create_outline_ready_project(client: TestClient) -> int:
    project_id = create_project(client)
    app.dependency_overrides[get_configured_llm_provider] = FakeLLMProvider
    response = client.post(
        f"/projects/{project_id}/outline",
        json={"idea": "程序员发现老板窃取了他的AI成果", "episode_count": 10},
    )
    assert response.status_code == 200
    return project_id


def generate_script(
    client: TestClient,
    project_id: int,
    episode_number: int = 1,
    provider=None,
    use_showrunner_brief: bool = False,
    run_showrunner_qc: bool = False,
    max_revision_attempts: int = 0,
):
    app.dependency_overrides[get_configured_llm_provider] = (
        provider or FakeLLMProvider
    )
    return client.post(
        f"/projects/{project_id}/episodes/{episode_number}/script",
        json={
            "target_duration_seconds": 90,
            "use_showrunner_brief": use_showrunner_brief,
            "run_showrunner_qc": run_showrunner_qc,
            "max_revision_attempts": max_revision_attempts,
        },
    )


def test_generate_first_script_validates_updates_and_persists(
    client: TestClient, test_session_local
) -> None:
    project_id = create_outline_ready_project(client)

    response = generate_script(client, project_id)

    assert response.status_code == 200
    body = response.json()
    script = body["script"]
    assert body["project_id"] == project_id
    assert body["episode_number"] == 1
    assert body["status"] == "script_ready"
    assert script["episode_number"] == 1
    assert [scene["scene_number"] for scene in script["scenes"]] == [1, 2, 3]

    allowed_ids = {"lin_feng", "su_yan", "gao_qi"}
    used_ids = {
        dialogue["character_id"]
        for scene in script["scenes"]
        for dialogue in scene["dialogues"]
    }
    assert used_ids <= allowed_ids

    with test_session_local() as db:
        project = db.scalar(select(Project).where(Project.id == project_id))
        assert project is not None
        assert project.status == "script_ready"
        scripts = json.loads(project.scripts_json)
        assert scripts["1"]["title"] == script["title"]
        memory = json.loads(project.memory_json)
        assert memory["episodes"]["1"]["episode_number"] == 1
        assert memory["episodes"]["1"]["summary"] == script["episode_goal"]
        assert script["ending_hook"] in memory["episodes"]["1"]["ending_hook"]


def test_regenerating_episode_overwrites_only_that_episode(
    client: TestClient, test_session_local
) -> None:
    project_id = create_outline_ready_project(client)
    first_provider = lambda: FakeLLMProvider(script_title="旧版剧本")
    second_provider = lambda: FakeLLMProvider(script_title="新版剧本")
    assert generate_script(client, project_id, provider=first_provider).status_code == 200

    response = generate_script(client, project_id, provider=second_provider)

    assert response.status_code == 200
    with test_session_local() as db:
        project = db.get(Project, project_id)
        scripts = json.loads(project.scripts_json)
        assert list(scripts) == ["1"]
        assert scripts["1"]["title"] == "新版剧本"


def test_generating_second_episode_preserves_first(
    client: TestClient, test_session_local
) -> None:
    project_id = create_outline_ready_project(client)
    assert generate_script(client, project_id).status_code == 200
    second_provider = lambda: FakeLLMProvider(script_episode_number=2)

    response = generate_script(client, project_id, 2, second_provider)

    assert response.status_code == 200
    with test_session_local() as db:
        project = db.get(Project, project_id)
        scripts = json.loads(project.scripts_json)
        assert set(scripts) == {"1", "2"}
        assert scripts["1"]["episode_number"] == 1
        assert scripts["2"]["episode_number"] == 2
        memory = json.loads(project.memory_json)
        assert set(memory["episodes"]) == {"1", "2"}


def test_get_saved_script(client: TestClient) -> None:
    project_id = create_outline_ready_project(client)
    assert generate_script(client, project_id).status_code == 200

    response = client.get(f"/projects/{project_id}/episodes/1/script")

    assert response.status_code == 200
    assert response.json()["script"]["episode_number"] == 1


def test_generate_script_returns_404_for_missing_project(client: TestClient) -> None:
    response = generate_script(client, 999999)
    assert response.status_code == 404


def test_generate_script_returns_409_without_outline(client: TestClient) -> None:
    project_id = create_project(client)
    response = generate_script(client, project_id)
    assert response.status_code == 409


def test_generate_script_returns_404_for_missing_episode(client: TestClient) -> None:
    project_id = create_outline_ready_project(client)
    response = generate_script(client, project_id, 11)
    assert response.status_code == 404


def test_generate_script_maps_provider_failure_to_502(client: TestClient) -> None:
    project_id = create_outline_ready_project(client)
    provider = lambda: FailingLLMProvider(LLMCallError("secret upstream detail"))

    response = generate_script(client, project_id, provider=provider)

    assert response.status_code == 502
    assert "secret" not in response.text


def test_generate_script_maps_context_schema_failure_to_502(
    client: TestClient,
) -> None:
    project_id = create_outline_ready_project(client)
    provider = lambda: FakeLLMProvider(script_character_id="unknown_person")

    response = generate_script(client, project_id, provider=provider)

    assert response.status_code == 502


def test_generate_script_rejects_llm_duration_outside_target_tolerance(
    client: TestClient,
) -> None:
    project_id = create_outline_ready_project(client)
    provider = lambda: FakeLLMProvider(script_duration_seconds=95)

    response = generate_script(client, project_id, provider=provider)

    assert response.status_code == 502


def test_writer_context_failure_logs_safe_reason_code(
    client: TestClient,
    tmp_path: Path,
) -> None:
    log_file = tmp_path / "app.jsonl"
    configure_logging(str(log_file))
    project_id = create_outline_ready_project(client)
    provider = lambda: FakeLLMProvider(script_duration_seconds=95)

    response = generate_script(client, project_id, provider=provider)

    assert response.status_code == 502
    records = read_recent_logs(log_file_path=str(log_file))
    failed = next(
        record
        for record in records
        if record["event"] == "workflow.writer.validation_failed"
    )
    assert failed["failure_reasons"] == ["duration_mismatch"]
    assert failed["actual_duration_seconds"] == 95
    assert failed["target_duration_seconds"] == 90
    assert "script" not in failed


def test_writer_retries_once_after_context_validation_failure(
    client: TestClient,
) -> None:
    class RepairingWriterProvider(FakeLLMProvider):
        def __init__(self) -> None:
            super().__init__()
            self.script_calls = 0

        def generate_structured(self, system_prompt, user_prompt, output_schema):
            if output_schema is EpisodeScript:
                self.script_calls += 1
                self.script_duration_seconds = (
                    95 if self.script_calls == 1 else 90
                )
            return super().generate_structured(
                system_prompt,
                user_prompt,
                output_schema,
            )

    project_id = create_outline_ready_project(client)
    provider = RepairingWriterProvider()

    response = generate_script(
        client,
        project_id,
        provider=lambda: provider,
    )

    assert response.status_code == 200
    assert provider.script_calls == 2
    assert "duration_mismatch" in provider.last_user_prompt


def test_generate_script_accepts_llm_singular_dialogue_key(
    client: TestClient,
) -> None:
    project_id = create_outline_ready_project(client)
    provider = lambda: FakeLLMProvider(script_dialogue_key="dialogue")

    response = generate_script(client, project_id, provider=provider)

    assert response.status_code == 200
    script = response.json()["script"]
    assert "dialogues" in script["scenes"][0]
    assert "dialogue" not in script["scenes"][0]


def test_generate_script_rejects_invalid_duration(client: TestClient) -> None:
    project_id = create_outline_ready_project(client)
    response = client.post(
        f"/projects/{project_id}/episodes/1/script",
        json={"target_duration_seconds": 30},
    )
    assert response.status_code == 422


def test_writer_uses_character_bibles_when_available(client: TestClient) -> None:
    project_id = create_outline_ready_project(client)
    app.dependency_overrides[get_configured_llm_provider] = FakeLLMProvider
    characters = client.post(
        f"/projects/{project_id}/characters/generate",
        json={},
    )
    assert characters.status_code == 200

    writer_provider = FakeLLMProvider()
    response = generate_script(
        client,
        project_id,
        provider=lambda: writer_provider,
    )

    assert response.status_code == 200
    writer_input = json.loads(writer_provider.last_user_prompt)
    assert writer_input["character_source"] == "character_bible"
    assert all("speech_style" in character for character in writer_input["characters"])
    assert all(
        "continuity_rules" in character for character in writer_input["characters"]
    )


def test_writer_falls_back_to_outline_characters_when_bibles_are_absent(
    client: TestClient,
) -> None:
    project_id = create_outline_ready_project(client)
    writer_provider = FakeLLMProvider()

    response = generate_script(
        client,
        project_id,
        provider=lambda: writer_provider,
    )

    assert response.status_code == 200
    writer_input = json.loads(writer_provider.last_user_prompt)
    assert writer_input["character_source"] == "outline"
    assert all("speech_style" not in character for character in writer_input["characters"])


def test_writer_receives_episode_boundary_context_for_first_episode(
    client: TestClient,
) -> None:
    project_id = create_outline_ready_project(client)
    writer_provider = FakeLLMProvider()

    response = generate_script(
        client,
        project_id,
        provider=lambda: writer_provider,
    )

    assert response.status_code == 200
    writer_input = json.loads(writer_provider.last_user_prompt)
    assert writer_input["previous_episode_outline"] is None
    assert writer_input["current_episode_outline"]["episode_number"] == 1
    assert writer_input["next_episode_outline"]["episode_number"] == 2


def test_writer_receives_episode_boundary_context_for_middle_episode(
    client: TestClient,
) -> None:
    project_id = create_outline_ready_project(client)
    assert generate_script(client, project_id).status_code == 200
    writer_provider = FakeLLMProvider(script_episode_number=2)

    response = generate_script(
        client,
        project_id,
        episode_number=2,
        provider=lambda: writer_provider,
    )

    assert response.status_code == 200
    writer_input = json.loads(writer_provider.last_user_prompt)
    assert writer_input["previous_episode_outline"]["episode_number"] == 1
    assert writer_input["current_episode_outline"]["episode_number"] == 2
    assert writer_input["next_episode_outline"]["episode_number"] == 3
    assert "summary" not in writer_input["next_episode_outline"]
    assert [
        episode["episode_number"]
        for episode in writer_input["story_outline"]["episodes"]
    ] == [1, 2]
    assert writer_input["story_memory"]["episodes"]["1"]["episode_number"] == 1
    assert writer_input["story_memory"]["episodes"]["1"]["summary"]


def test_regenerating_episode_prunes_later_story_memory(
    client: TestClient,
    test_session_local,
) -> None:
    project_id = create_outline_ready_project(client)
    assert generate_script(client, project_id).status_code == 200
    assert (
        generate_script(
            client,
            project_id,
            episode_number=2,
            provider=lambda: FakeLLMProvider(script_episode_number=2),
        ).status_code
        == 200
    )

    response = generate_script(
        client,
        project_id,
        provider=lambda: FakeLLMProvider(script_title="重写第一集"),
    )

    assert response.status_code == 200
    with test_session_local() as db:
        project = db.get(Project, project_id)
        memory = json.loads(project.memory_json)
        assert set(memory["episodes"]) == {"1"}


def test_writer_receives_memory_backfilled_from_legacy_saved_scripts(
    client: TestClient,
    test_session_local,
) -> None:
    project_id = create_outline_ready_project(client)
    with test_session_local() as db:
        project = db.get(Project, project_id)
        project.scripts_json = json.dumps(
            {"1": valid_script_data()},
            ensure_ascii=False,
        )
        project.memory_json = None
        db.commit()

    writer_provider = FakeLLMProvider(script_episode_number=2)
    response = generate_script(
        client,
        project_id,
        episode_number=2,
        provider=lambda: writer_provider,
    )

    assert response.status_code == 200
    writer_input = json.loads(writer_provider.last_user_prompt)
    assert writer_input["story_memory"]["episodes"]["1"]["summary"]


def test_writer_uses_v2_prompt_with_continuity_guardrails(
    client: TestClient,
) -> None:
    project_id = create_outline_ready_project(client)
    writer_provider = FakeLLMProvider()

    response = generate_script(
        client,
        project_id,
        provider=lambda: writer_provider,
    )

    assert response.status_code == 200
    assert "Writer Agent v2" in writer_provider.last_system_prompt
    assert "后续集" in writer_provider.last_system_prompt
    assert "道具" in writer_provider.last_system_prompt
    assert "临时发明" in writer_provider.last_system_prompt
    assert "触发瞬间" in writer_provider.last_system_prompt
    assert "不能写入 `characters` 数组" in writer_provider.last_system_prompt


def test_writer_can_receive_saved_showrunner_brief_when_requested(
    client: TestClient,
) -> None:
    project_id = create_outline_ready_project(client)
    app.dependency_overrides[get_configured_llm_provider] = FakeLLMProvider
    assert client.post(f"/projects/{project_id}/characters/generate", json={}).status_code == 200
    assert client.post(f"/projects/{project_id}/showrunner", json={}).status_code == 200
    assert (
        client.post(
            f"/projects/{project_id}/episodes/1/writer-brief",
            json={"target_duration_seconds": 90},
        ).status_code
        == 200
    )
    writer_provider = FakeLLMProvider()

    response = generate_script(
        client,
        project_id,
        provider=lambda: writer_provider,
        use_showrunner_brief=True,
    )

    assert response.status_code == 200
    writer_input = json.loads(writer_provider.last_user_prompt)
    assert writer_input["writer_brief"]["episode_number"] == 1
    assert writer_input["writer_brief"]["required_beats"]
    assert writer_input["writer_brief"]["forbidden_content"]


def test_writer_brief_is_not_sent_when_flag_is_false(client: TestClient) -> None:
    project_id = create_outline_ready_project(client)
    writer_provider = FakeLLMProvider()

    response = generate_script(
        client,
        project_id,
        provider=lambda: writer_provider,
        use_showrunner_brief=False,
    )

    assert response.status_code == 200
    writer_input = json.loads(writer_provider.last_user_prompt)
    assert writer_input["writer_brief"] is None


def test_generate_script_with_showrunner_brief_requires_saved_brief(
    client: TestClient,
) -> None:
    project_id = create_outline_ready_project(client)
    app.dependency_overrides[get_configured_llm_provider] = FakeLLMProvider
    assert client.post(f"/projects/{project_id}/characters/generate", json={}).status_code == 200
    assert client.post(f"/projects/{project_id}/showrunner", json={}).status_code == 200

    response = generate_script(
        client,
        project_id,
        use_showrunner_brief=True,
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Writer brief not found"}


def prepare_showrunner_brief_project(client: TestClient) -> int:
    project_id = create_outline_ready_project(client)
    app.dependency_overrides[get_configured_llm_provider] = FakeLLMProvider
    assert client.post(f"/projects/{project_id}/characters/generate", json={}).status_code == 200
    assert client.post(f"/projects/{project_id}/showrunner", json={}).status_code == 200
    assert (
        client.post(
            f"/projects/{project_id}/episodes/1/writer-brief",
            json={"target_duration_seconds": 90},
        ).status_code
        == 200
    )
    return project_id


def test_showrunner_qc_pass_saves_script_memory_and_qc_report(
    client: TestClient,
    test_session_local,
) -> None:
    project_id = prepare_showrunner_brief_project(client)
    provider = lambda: FakeLLMProvider(qc_status="pass")

    response = generate_script(
        client,
        project_id,
        provider=provider,
        use_showrunner_brief=True,
        run_showrunner_qc=True,
    )

    assert response.status_code == 200
    with test_session_local() as db:
        project = db.get(Project, project_id)
        scripts = json.loads(project.scripts_json)
        memory = json.loads(project.memory_json)
        showrunner = json.loads(project.showrunner_json)
        assert "1" in scripts
        assert "1" in memory["episodes"]
        assert memory["episodes"]["1"]["source"] == "qc_approved"
        assert memory["episodes"]["1"]["ending_state"]["location"]
        assert showrunner["qc_reports"]["1"]["status"] == "pass"
        assert showrunner["qc_reports"]["1"]["approved_memory"]["source"] == "qc_approved"


def test_showrunner_qc_rejects_ungrounded_approved_memory(
    client: TestClient,
    test_session_local,
) -> None:
    class UngroundedQCProvider(FakeLLMProvider):
        def generate_structured(self, system_prompt, user_prompt, output_schema):
            if output_schema is QCReport:
                data = valid_qc_pass_report_data()
                data["memory_evidence"] = []
                return QCReport.model_validate(data)
            return super().generate_structured(
                system_prompt,
                user_prompt,
                output_schema,
            )

    project_id = prepare_showrunner_brief_project(client)

    response = generate_script(
        client,
        project_id,
        provider=UngroundedQCProvider,
        use_showrunner_brief=True,
        run_showrunner_qc=True,
    )

    assert response.status_code == 502
    with test_session_local() as db:
        project = db.get(Project, project_id)
        assert project.scripts_json is None
        assert project.memory_json is None


def test_showrunner_qc_retries_once_after_ungrounded_memory(
    client: TestClient,
) -> None:
    class GroundingRetryProvider(FakeLLMProvider):
        def __init__(self) -> None:
            super().__init__(qc_status="pass")
            self.qc_calls = 0

        def generate_structured(self, system_prompt, user_prompt, output_schema):
            if output_schema is QCReport:
                self.qc_calls += 1
                if self.qc_calls == 1:
                    data = valid_qc_pass_report_data()
                    data["memory_evidence"] = []
                    return QCReport.model_validate(data)
            return super().generate_structured(
                system_prompt,
                user_prompt,
                output_schema,
            )

    project_id = prepare_showrunner_brief_project(client)
    provider = GroundingRetryProvider()

    response = generate_script(
        client,
        project_id,
        provider=lambda: provider,
        use_showrunner_brief=True,
        run_showrunner_qc=True,
    )

    assert response.status_code == 200
    assert provider.qc_calls == 2


def test_showrunner_qc_completes_missing_unresolved_question_obligation(
    client: TestClient,
    test_session_local,
) -> None:
    class MissingObligationQCProvider(FakeLLMProvider):
        def generate_structured(self, system_prompt, user_prompt, output_schema):
            if output_schema is QCReport:
                data = valid_qc_pass_report_data()
                data["approved_memory"]["continuity_obligations"] = []
                data["memory_evidence"] = [
                    item
                    for item in data["memory_evidence"]
                    if not item["memory_path"].startswith("continuity_obligations.")
                ]
                return QCReport.model_validate(data)
            return super().generate_structured(
                system_prompt,
                user_prompt,
                output_schema,
            )

    project_id = prepare_showrunner_brief_project(client)

    response = generate_script(
        client,
        project_id,
        provider=MissingObligationQCProvider,
        use_showrunner_brief=True,
        run_showrunner_qc=True,
    )

    assert response.status_code == 200
    with test_session_local() as db:
        project = db.get(Project, project_id)
        memory = json.loads(project.memory_json)
        obligations = memory["episodes"]["1"]["continuity_obligations"]
        assert len(obligations) == 1
        assert obligations[0] == {
            "obligation_id": "e1_unresolved_question_1",
            "kind": "active_crisis",
            "description": "日志中的名字为何出现。",
            "source_episode_number": 1,
            "due_episode_number": 2,
            "source_memory_path": "unresolved_questions.0",
        }


def test_cross_episode_contract_is_resolved_before_second_script_is_saved(
    client: TestClient,
    test_session_local,
) -> None:
    project_id = prepare_showrunner_brief_project(client)
    assert (
        generate_script(
            client,
            project_id,
            provider=lambda: FakeLLMProvider(qc_status="pass"),
            use_showrunner_brief=True,
            run_showrunner_qc=True,
        ).status_code
        == 200
    )
    app.dependency_overrides[get_configured_llm_provider] = lambda: FakeLLMProvider(
        writer_brief_episode_number=2
    )
    brief_response = client.post(
        f"/projects/{project_id}/episodes/2/writer-brief",
        json={"target_duration_seconds": 90},
    )
    assert brief_response.status_code == 200
    assert brief_response.json()["brief"]["continuity_contract"] is not None

    response = generate_script(
        client,
        project_id,
        episode_number=2,
        provider=lambda: FakeLLMProvider(
            script_episode_number=2,
            writer_brief_episode_number=2,
            qc_status="pass",
        ),
        use_showrunner_brief=True,
        run_showrunner_qc=True,
    )

    assert response.status_code == 200
    with test_session_local() as db:
        project = db.get(Project, project_id)
        showrunner = json.loads(project.showrunner_json)
        report = showrunner["qc_reports"]["2"]
        assert {
            item["obligation_id"]
            for item in report["continuity_resolutions"]
        } == {"episode_1_ending_state", "e1_trace_the_name"}
        assert "2" in json.loads(project.memory_json)["episodes"]


def test_showrunner_qc_fail_does_not_save_script_or_memory_but_stores_report(
    client: TestClient,
    test_session_local,
) -> None:
    project_id = prepare_showrunner_brief_project(client)
    provider = lambda: FakeLLMProvider(qc_status="fail")

    response = generate_script(
        client,
        project_id,
        provider=provider,
        use_showrunner_brief=True,
        run_showrunner_qc=True,
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Showrunner QC did not pass"}
    with test_session_local() as db:
        project = db.get(Project, project_id)
        assert project.scripts_json is None
        assert project.memory_json is None
        showrunner = json.loads(project.showrunner_json)
        assert showrunner["qc_reports"]["1"]["status"] == "fail"

    qc_response = client.get(f"/projects/{project_id}/episodes/1/showrunner-qc")
    assert qc_response.status_code == 200
    assert qc_response.json()["report"]["status"] == "fail"


def test_showrunner_qc_requires_brief_mode(client: TestClient) -> None:
    project_id = prepare_showrunner_brief_project(client)

    response = generate_script(
        client,
        project_id,
        provider=lambda: FakeLLMProvider(qc_status="pass"),
        use_showrunner_brief=False,
        run_showrunner_qc=True,
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Showrunner QC requires writer brief"}


def test_showrunner_qc_rejects_invalid_revision_attempt_count(
    client: TestClient,
) -> None:
    project_id = prepare_showrunner_brief_project(client)

    response = generate_script(
        client,
        project_id,
        provider=lambda: FakeLLMProvider(qc_status="pass"),
        use_showrunner_brief=True,
        run_showrunner_qc=True,
        max_revision_attempts=3,
    )

    assert response.status_code == 422


def test_showrunner_qc_can_revise_once_then_save_only_passing_script(
    client: TestClient,
    test_session_local,
) -> None:
    class RevisionProvider(FakeLLMProvider):
        def __init__(self) -> None:
            super().__init__(qc_status="fail")
            self.qc_statuses = ["fail", "pass"]
            self.writer_inputs: list[dict] = []

        def generate_structured(self, system_prompt, user_prompt, output_schema):
            if output_schema is QCReport:
                self.qc_status = self.qc_statuses.pop(0)
            if output_schema is EpisodeScript:
                self.writer_inputs.append(json.loads(user_prompt))
            return super().generate_structured(
                system_prompt,
                user_prompt,
                output_schema,
            )

    project_id = prepare_showrunner_brief_project(client)
    provider = RevisionProvider()

    response = generate_script(
        client,
        project_id,
        provider=lambda: provider,
        use_showrunner_brief=True,
        run_showrunner_qc=True,
        max_revision_attempts=1,
    )

    assert response.status_code == 200
    assert len(provider.writer_inputs) == 2
    assert provider.writer_inputs[0]["revision_feedback"] is None
    assert provider.writer_inputs[1]["revision_feedback"][0]["code"] == "future_reveal"
    with test_session_local() as db:
        project = db.get(Project, project_id)
        showrunner = json.loads(project.showrunner_json)
        memory = json.loads(project.memory_json)
        assert showrunner["qc_reports"]["1"]["status"] == "pass"
        assert memory["episodes"]["1"]["source"] == "qc_approved"


def test_showrunner_qc_accumulates_feedback_across_revisions(
    client: TestClient,
) -> None:
    class RevisionProvider(FakeLLMProvider):
        def __init__(self) -> None:
            super().__init__(qc_status="fail")
            self.qc_call_number = 0
            self.writer_inputs: list[dict] = []

        def generate_structured(self, system_prompt, user_prompt, output_schema):
            if output_schema is EpisodeScript:
                self.writer_inputs.append(json.loads(user_prompt))
            if output_schema is QCReport:
                self.qc_call_number += 1
                if self.qc_call_number == 1:
                    self.qc_status = "fail"
                elif self.qc_call_number == 2:
                    data = valid_qc_report_data()
                    data["issues"][0]["code"] = "opening_hook_not_realized"
                    return QCReport.model_validate(data)
                else:
                    self.qc_status = "pass"
            return super().generate_structured(
                system_prompt,
                user_prompt,
                output_schema,
            )

    project_id = prepare_showrunner_brief_project(client)
    provider = RevisionProvider()

    response = generate_script(
        client,
        project_id,
        provider=lambda: provider,
        use_showrunner_brief=True,
        run_showrunner_qc=True,
        max_revision_attempts=2,
    )

    assert response.status_code == 200
    assert len(provider.writer_inputs) == 3
    third_feedback_codes = {
        issue["code"] for issue in provider.writer_inputs[2]["revision_feedback"]
    }
    assert third_feedback_codes == {"future_reveal", "opening_hook_not_realized"}
