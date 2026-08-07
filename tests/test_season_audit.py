"""season_audit 工具的核心逻辑测试（纯单元，不依赖真实数据）。"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.season_audit import (
    _contains_any,
    _keywords,
    check_hook_continuation,
    check_obligation_closure,
    check_plan_fulfillment,
    check_structure,
)


# ---------- 文本匹配 ----------

def test_keywords_sliding_window_handles_odd_length() -> None:
    """奇数长度句子用滑动窗口切 2 字词元，不应错位丢词。"""
    keywords = _keywords("见面时发现对方是李瑶。")
    assert "李瑶" in keywords
    assert "见面" in keywords


def test_contains_any_partial_match_pass() -> None:
    """部分兑现（插字变体）应通过：'警察到达了门外' 匹配 '警察到达门外'。"""
    assert _contains_any("警察已经到达了门外", _keywords("警察到达门外"))


def test_contains_any_missing_beat_fails() -> None:
    """核心词元缺失应判为未兑现。"""
    assert not _contains_any("两人在咖啡店聊天", _keywords("李瑶拒绝合作设下陷阱"))


# ---------- 检查 A：义务闭合 ----------

def test_obligation_closure_flags_unclosed_mid_season() -> None:
    """来源第 3 集的义务在第 4-10 集均未 resolved → P0。"""
    memory = {
        "episodes": {
            "3": {
                "continuity_obligations": [
                    {
                        "obligation_id": "e3_hidden_evidence",
                        "source_episode_number": 3,
                        "description": "找到隐藏证据。",
                    }
                ]
            },
            "10": {"continuity_obligations": []},
        }
    }
    showrunner = {"qc_reports": {"4": {"continuity_resolutions": []}}}
    findings = check_obligation_closure(memory, showrunner)
    assert any(f["level"] == "P0" and f["code"] == "obligation_unclosed" for f in findings)


def test_obligation_closure_accepts_resolved() -> None:
    """义务在后续集被 resolved → 不报。"""
    memory = {
        "episodes": {
            "3": {
                "continuity_obligations": [
                    {
                        "obligation_id": "e3_hidden_evidence",
                        "source_episode_number": 3,
                        "description": "找到隐藏证据。",
                    }
                ]
            }
        }
    }
    showrunner = {
        "qc_reports": {
            "4": {
                "continuity_resolutions": [
                    {"obligation_id": "e3_hidden_evidence", "status": "resolved"}
                ]
            }
        }
    }
    findings = check_obligation_closure(memory, showrunner)
    assert not any(f["code"] == "obligation_unclosed" for f in findings)


def test_obligation_closure_finale_relaxed() -> None:
    """结局期（ep9/10 来源）义务未闭合只降级为 P2，不报 P0。"""
    memory = {
        "episodes": {
            "9": {
                "continuity_obligations": [
                    {
                        "obligation_id": "e9_aftermath",
                        "source_episode_number": 9,
                        "description": "结局余波。",
                    }
                ]
            },
            "10": {"continuity_obligations": []},
        }
    }
    showrunner = {"qc_reports": {}}
    findings = check_obligation_closure(memory, showrunner)
    assert not any(f["level"] == "P0" for f in findings)
    assert any(f["code"] == "finale_obligation_open" for f in findings)


# ---------- 检查 B：计划兑现 ----------

def test_plan_fulfillment_missing_beat_flagged() -> None:
    """计划节拍在剧本中完全缺失 → P1。"""
    showrunner = {
        "episode_plan": [
            {
                "episode_number": 1,
                "must_include": ["李瑶拒绝合作设下陷阱考验陈默"],
            }
        ]
    }
    scripts = {
        "1": {
            "episode_number": 1,
            "scenes": [
                {
                    "scene_number": 1,
                    "location": "咖啡店",
                    "time_of_day": "白天",
                    "characters": [],
                    "scene_goal": "闲聊",
                    "action": "两人聊天。",
                    "dialogues": [
                        {
                            "character_id": "a",
                            "character_name": "甲",
                            "emotion": "平静",
                            "line": "今天的咖啡不错。",
                            "action_note": "",
                        }
                    ],
                    "transition": "",
                }
            ],
        }
    }
    findings = check_plan_fulfillment(showrunner, scripts)
    assert any(f["code"] == "plan_beat_missing" for f in findings)


def test_plan_fulfillment_beat_present_pass() -> None:
    """计划节拍在剧本中出现 → 不报。"""
    showrunner = {
        "episode_plan": [
            {"episode_number": 1, "must_include": ["警察到达门外"]}
        ]
    }
    scripts = {
        "1": {
            "episode_number": 1,
            "scenes": [
                {
                    "scene_number": 1,
                    "location": "公寓",
                    "time_of_day": "凌晨",
                    "characters": [],
                    "scene_goal": "被围",
                    "action": "警察到达了门外，用力敲门。",
                    "dialogues": [],
                    "transition": "",
                }
            ],
        }
    }
    findings = check_plan_fulfillment(showrunner, scripts)
    assert not any(f["code"] == "plan_beat_missing" for f in findings)


# ---------- 检查 C：钩子承接 ----------

def test_hook_continuation_flagged_when_missing() -> None:
    """ep1 的 ending_hook 在 ep2 无承接 → P1。"""
    memory = {
        "episodes": {
            "1": {"ending_hook": "陈默将钥匙藏进口袋，身后房门被警察撞开"},
            "2": {},
        }
    }
    scripts = {
        "2": {
            "episode_number": 2,
            "scenes": [
                {
                    "scene_number": 1,
                    "location": "街道",
                    "time_of_day": "白天",
                    "characters": [],
                    "scene_goal": "逃亡",
                    "action": "陈默在街上奔跑。",
                    "dialogues": [],
                    "transition": "",
                }
            ],
        }
    }
    findings = check_hook_continuation(memory, scripts)
    assert any(f["code"] == "hook_not_continued" for f in findings)


def test_hook_continuation_present_pass() -> None:
    """ep1 的 ending_hook 在 ep2 被承接 → 不报。"""
    memory = {
        "episodes": {
            "1": {"ending_hook": "陈默将钥匙藏进口袋，身后房门被警察撞开"},
            "2": {},
        }
    }
    scripts = {
        "2": {
            "episode_number": 2,
            "scenes": [
                {
                    "scene_number": 1,
                    "location": "公寓",
                    "time_of_day": "凌晨",
                    "characters": [],
                    "scene_goal": "脱困",
                    "action": "警察用力撞开房门，陈默趁乱从窗户翻出，钥匙仍紧握在手中。",
                    "dialogues": [],
                    "transition": "",
                }
            ],
        }
    }
    findings = check_hook_continuation(memory, scripts)
    assert not any(f["code"] == "hook_not_continued" for f in findings)


# ---------- 检查 D：结构健康 ----------

def test_structure_flags_too_many_scenes() -> None:
    """8 个场景 → P2 too_many_scenes。"""
    scripts = {
        "1": {
            "episode_number": 1,
            "duration_seconds": 600,
            "opening_hook": "开场",
            "ending_hook": "结尾",
            "scenes": [{"scene_number": i} for i in range(1, 9)],
        }
    }
    findings = check_structure(scripts)
    assert any(f["code"] == "too_many_scenes" for f in findings)


def test_structure_normal_pass() -> None:
    """正常单集 → 无结构告警。"""
    scripts = {
        "1": {
            "episode_number": 1,
            "duration_seconds": 600,
            "opening_hook": "开场",
            "ending_hook": "结尾",
            "scenes": [{"scene_number": i} for i in range(1, 5)],
        }
    }
    findings = check_structure(scripts)
    assert findings == []
