from pathlib import Path


def test_qc_prompt_defines_non_empty_continuity_resolution_contract() -> None:
    prompt = Path("app/prompts/qc_v1.md").read_text(encoding="utf-8")

    assert '"obligation_id": "episode_1_ending_state"' in prompt
    assert '"status": "resolved"' in prompt
    assert '"scene_number": 1' in prompt
    assert '"evidence_text": "屏幕上的名字仍在闪烁"' in prompt


def test_qc_prompt_defines_strict_memory_field_shapes() -> None:
    prompt = Path("app/prompts/qc_v1.md").read_text(encoding="utf-8")

    assert "`relationship_changes` 必须是中文字符串数组" in prompt
    assert (
        "`continuity_obligations.N.kind` 只能是 `ending_state`、"
        "`active_crisis`、`promise` 或 `prop_or_evidence`" in prompt
    )


def test_qc_prompt_requires_exact_evidence_catalog_selection() -> None:
    prompt = Path("app/prompts/qc_v1.md").read_text(encoding="utf-8")

    assert "`evidence_catalog`：后端从剧本场景提取的允许引用证据清单" in prompt
    assert (
        "必须完整复制同一条清单中的 `scene_number` 和 `evidence_text`"
        in prompt
    )
    assert "不得概括、改写、拼接或缩短证据文字" in prompt
    assert "`knows` 必须始终输出中文字符串数组" in prompt
    assert "`ending_state_reference`：后端确定的最后一场地点和时间" in prompt
    assert "必须原样复制 `ending_state_reference.location`" in prompt


def test_qc_prompt_defines_carried_forward_writeback_contract() -> None:
    prompt = Path("app/prompts/qc_v1.md").read_text(encoding="utf-8")

    assert "status=carried_forward" in prompt
    assert "第 10 集不得使用 `carried_forward`" in prompt
    assert "必须出现在本集 `approved_memory.continuity_obligations` 中" in prompt
    assert "`source_episode_number` 为当前集号" in prompt
    assert "`due_episode_number` 为下一集号即可" in prompt
    assert "后端会按上一集合同把 `source_episode_number` 恢复为义务的原始来源集" in prompt
    assert "不得沿用上一集记忆的路径" in prompt
    assert "resolved` 的事项不得再次写入本集" in prompt


def test_qc_prompt_contains_non_empty_carried_forward_json_example() -> None:
    prompt = Path("app/prompts/qc_v1.md").read_text(encoding="utf-8")

    assert '"status": "carried_forward"' in prompt
    assert '"obligation_id": "e1_trace_log_name"' in prompt
    assert '"source_episode_number": 2' in prompt
    assert '"due_episode_number": 3' in prompt
    assert '"source_memory_path": "unresolved_questions.0"' in prompt
    assert '"memory_path": "continuity_obligations.0"' in prompt
    assert '"evidence_text": "屏幕上跳出苏妍父亲的名字"' in prompt


def test_qc_prompt_carried_forward_example_source_path_is_internal() -> None:
    prompt = Path("app/prompts/qc_v1.md").read_text(encoding="utf-8")

    example = prompt.split("`carried_forward` 的最小完整示例")[-1]
    # 来源路径 unresolved_questions.0 必须真实存在于示例 approved_memory 内
    assert '"unresolved_questions": ["日志中的异常名字为何出现。"]' in example
    # memory_evidence 必须同时包含来源路径与义务路径两条本集证据
    assert '"memory_path": "unresolved_questions.0"' in example
    assert '"memory_path": "continuity_obligations.0"' in example
    # 两条证据 + 决议的场号与原文必须逐字一致（同一 evidence_catalog 记录）
    assert example.count('"evidence_text": "屏幕上跳出苏妍父亲的名字"') == 3
    assert example.count('"scene_number": 2') == 3
