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
