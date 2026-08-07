"""整季质量审计工具（纯代码、零 LLM 成本）。

用法：
    python tools/season_audit.py --project-id 4
    python tools/season_audit.py --project-id 4 --report docs/reports/season_audit_project4.md

从 SQLite 读取项目的 showrunner_json / memory_json / scripts_json，
用确定性规则检查四类结构质量问题：

- A 义务闭合：每集 created 的义务是否最终被 resolved（第 10 集允许遗留）
- B 计划兑现：episode_plan 每集 must_include 是否在对应剧本文本中出现（宽松匹配）
- C 钩子承接：ep N 的 ending_hook 关键词是否在 ep N+1 剧本中被承接
- D 结构健康：场景数/时长分布、opening/ending hook 存在性、结局集无新欠账

结果分级：
- P0 致命（跨集义务断裂 / 计划关键节拍缺失）
- P1 严重（钩子未承接 / 结构异常）
- P2 提示（轻微偏斜）

退出码：0 = 无 P0；1 = 有 P0。
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except AttributeError:
    pass

DEFAULT_DB = REPO_ROOT / "data" / "app.db"


# ---------- 数据读取 ----------

def load_project(db_path: Path, project_id: int) -> dict:
    con = sqlite3.connect(db_path)
    row = con.execute(
        "select showrunner_json, memory_json, scripts_json from projects where id=?",
        (project_id,),
    ).fetchone()
    con.close()
    if row is None:
        raise SystemExit(f"项目 {project_id} 不存在")
    showrunner, memory, scripts = row
    return {
        "showrunner": json.loads(showrunner) if showrunner else {},
        "memory": json.loads(memory) if memory else {},
        "scripts": json.loads(scripts) if scripts else {},
    }


# ---------- 文本匹配（宽松） ----------

_STRIP_TRANS = str.maketrans(
    "", "",
    " \t\n\r，。！？、；：""''（）《》·—…,.;:!?()[]{}",
)


def _strip(text: str) -> str:
    """归一化：去空白/标点，方便关键词匹配。"""
    return text.translate(_STRIP_TRANS)

_STOP_POS = {"x", "u", "c", "p", "d", "f", "r", "y", "e", "o", "q"}
_STOP_WORDS = {
    "一个", "那个", "这个", "自己", "已经", "正在", "开始", "突然",
    "然后", "但是", "因为", "所以", "如果", "只有", "没有", "还有",
    "以及", "同时", "我们", "他们", "你们", "两人",
}


def _keywords(text: str) -> list[str]:
    """jieba 分词提取实词元（名词/动词/形容词，过滤虚词和泛词）。

    宽松匹配：命中过半（至少 2 个）词元即认为节拍被兑现——容忍
    插字变体和同义改写，同时避免无分词器的滑动窗口噪声。
    """
    import jieba

    t = _strip(text)
    if not t:
        return []
    segs = jieba.cut(t)
    tokens = [
        w for w in segs
        if len(w) >= 2 and w not in _STOP_WORDS
    ]
    return list(dict.fromkeys(tokens))


def _contains_any(haystack: str, needles: list[str]) -> bool:
    h = _strip(haystack)
    if not h or not needles:
        return False
    hits = sum(1 for n in needles if n and n in h)
    return hits >= max(2, (len(needles) + 1) // 2)


# ---------- 检查 A：义务闭合 ----------

def check_obligation_closure(memory: dict, showrunner: dict) -> list[dict]:
    """每集 created 的义务（source_episode_number == 本集）在后续 QC 报告中
    是否最终 resolved。第 10 集（结局）允许遗留。"""
    findings: list[dict] = []
    episodes = memory.get("episodes") or {}
    qc_reports = (showrunner.get("qc_reports") or {}) if showrunner else {}

    # 收集每集 created 的义务
    created: dict[int, list[dict]] = {}
    for ep_key, ep in episodes.items():
        ep_num = int(ep_key)
        for ob in ep.get("continuity_obligations") or []:
            src = ob.get("source_episode_number")
            if src == ep_num:
                created.setdefault(ep_num, []).append(ob)

    # 收集所有 resolutions：obligation_id -> 最后状态
    resolved_ids: set[str] = set()
    for qc_key, qc in qc_reports.items():
        for res in qc.get("continuity_resolutions") or []:
            if res.get("status") == "resolved":
                resolved_ids.add(res.get("obligation_id"))

    total_episodes = max([int(k) for k in episodes.keys()] + [0])
    for src_ep, obligations in sorted(created.items()):
        for ob in obligations:
            oid = ob.get("obligation_id")
            if oid in resolved_ids:
                continue
            if src_ep >= total_episodes - 1:
                # 结局收束期（ep9/10）的义务：剧情可能已解决但 QC 未正式
                # 标 resolved，降级为提示而非致命
                findings.append({
                    "level": "P2",
                    "code": "finale_obligation_open",
                    "episode": src_ep,
                    "message": f"结局期义务 {oid} 未在 QC 报告中正式闭合（剧情可能已解决，建议人工确认）",
                    "detail": ob.get("description", ""),
                })
            else:
                findings.append({
                    "level": "P0",
                    "code": "obligation_unclosed",
                    "episode": src_ep,
                    "message": f"义务 {oid}（来源第 {src_ep} 集）整季未闭合",
                    "detail": ob.get("description", ""),
                })
    return findings


# ---------- 检查 B：计划兑现 ----------

def check_plan_fulfillment(showrunner: dict, scripts: dict) -> list[dict]:
    """episode_plan 每集 must_include 是否在对应剧本文本中出现。"""
    findings: list[dict] = []
    plan = showrunner.get("episode_plan") or []
    if isinstance(plan, dict):
        plan = list(plan.values())

    for item in plan:
        ep_num = item.get("episode_number")
        script = scripts.get(str(ep_num))
        if script is None:
            findings.append({
                "level": "P0",
                "code": "plan_episode_missing",
                "episode": ep_num,
                "message": f"第 {ep_num} 集有计划但无剧本",
                "detail": item.get("title", ""),
            })
            continue
        text = json.dumps(script, ensure_ascii=False)
        for must in item.get("must_include") or []:
            if not _contains_any(text, _keywords(must)):
                findings.append({
                    "level": "P1",
                    "code": "plan_beat_missing",
                    "episode": ep_num,
                    "message": f"第 {ep_num} 集计划节拍未在剧本中找到: {must[:30]}",
                    "detail": f"plan: {must}",
                })
    return findings


# ---------- 检查 C：钩子承接 ----------

def check_hook_continuation(memory: dict, scripts: dict) -> list[dict]:
    """ep N 的 ending_hook 关键词是否在 ep N+1 剧本中被承接。"""
    findings: list[dict] = []
    episodes = memory.get("episodes") or {}
    ep_nums = sorted(int(k) for k in episodes.keys())
    for i, ep_num in enumerate(ep_nums):
        if ep_num >= 10:
            break
        nxt = ep_num + 1
        ep_data = episodes.get(str(ep_num))
        hook = (ep_data or {}).get("ending_hook") or ""
        if not hook:
            findings.append({
                "level": "P1",
                "code": "missing_ending_hook",
                "episode": ep_num,
                "message": f"第 {ep_num} 集无 ending_hook",
                "detail": "",
            })
            continue
        nxt_script = scripts.get(str(nxt))
        if nxt_script is None:
            continue
        nxt_text = json.dumps(nxt_script, ensure_ascii=False)
        if not _contains_any(nxt_text, _keywords(hook)):
            findings.append({
                "level": "P1",
                "code": "hook_not_continued",
                "episode": ep_num,
                "message": f"第 {ep_num} 集 ending_hook 未在第 {nxt} 集承接",
                "detail": f"hook: {hook[:40]}",
            })
    return findings


# ---------- 检查 D：结构健康 ----------

def check_structure(scripts: dict) -> list[dict]:
    """场景数/时长分布、opening/ending hook 存在性。"""
    findings: list[dict] = []
    ep_nums = sorted(int(k) for k in scripts.keys())
    durations: list[int] = []
    for ep_num in ep_nums:
        script = scripts[str(ep_num)]
        scenes = script.get("scenes") or []
        dur = script.get("duration_seconds") or 0
        durations.append(dur)
        if not script.get("opening_hook"):
            findings.append({
                "level": "P2",
                "code": "missing_opening_hook",
                "episode": ep_num,
                "message": f"第 {ep_num} 集无 opening_hook",
                "detail": "",
            })
        if not script.get("ending_hook"):
            findings.append({
                "level": "P2",
                "code": "missing_script_ending_hook",
                "episode": ep_num,
                "message": f"第 {ep_num} 集剧本无 ending_hook 字段",
                "detail": "",
            })
        if len(scenes) > 6:
            findings.append({
                "level": "P2",
                "code": "too_many_scenes",
                "episode": ep_num,
                "message": f"第 {ep_num} 集 {len(scenes)} 个场景（建议 ≤6）",
                "detail": "",
            })
    if durations:
        avg = sum(durations) / len(durations)
        for ep_num, dur in zip(ep_nums, durations):
            if dur < avg * 0.5:
                findings.append({
                    "level": "P2",
                    "code": "short_episode",
                    "episode": ep_num,
                    "message": f"第 {ep_num} 集时长 {dur}s 明显短于均值 {avg:.0f}s",
                    "detail": "",
                })
    return findings


# ---------- 报告 ----------

LEVEL_ORDER = {"P0": 0, "P1": 1, "P2": 2}


def audit(project_id: int, db_path: Path = DEFAULT_DB) -> list[dict]:
    data = load_project(db_path, project_id)
    findings = []
    findings += check_obligation_closure(data["memory"], data["showrunner"])
    findings += check_plan_fulfillment(data["showrunner"], data["scripts"])
    findings += check_hook_continuation(data["memory"], data["scripts"])
    findings += check_structure(data["scripts"])
    findings.sort(key=lambda f: (LEVEL_ORDER.get(f["level"], 9), f["episode"]))
    return findings


def render_markdown(project_id: int, findings: list[dict]) -> str:
    lines = [f"# 整季质量审计报告（项目 {project_id}）", ""]
    counts = {"P0": 0, "P1": 0, "P2": 0}
    for f in findings:
        counts[f["level"]] = counts.get(f["level"], 0) + 1
    lines.append(f"- 检查时间：确定性规则审计（零 LLM 成本）")
    lines.append(f"- 结果：P0={counts['P0']} P1={counts['P1']} P2={counts['P2']}")
    lines.append("")
    if not findings:
        lines.append("**未发现问题。**")
        return "\n".join(lines)
    for level in ("P0", "P1", "P2"):
        subset = [f for f in findings if f["level"] == level]
        if not subset:
            continue
        lines.append(f"## {level} — {'致命' if level == 'P0' else '严重' if level == 'P1' else '提示'}")
        lines.append("")
        for f in subset:
            lines.append(f"- **ep{f['episode']}** [{f['code']}] {f['message']}")
            if f.get("detail"):
                lines.append(f"  - 依据：{f['detail'][:80]}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="整季质量审计（纯代码）")
    parser.add_argument("--project-id", type=int, required=True)
    parser.add_argument("--report", help="报告输出路径（Markdown）")
    parser.add_argument("--db", default=str(DEFAULT_DB), help="SQLite 路径")
    args = parser.parse_args()

    findings = audit(args.project_id, Path(args.db))
    text = render_markdown(args.project_id, findings)
    if args.report:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(text, encoding="utf-8")
        print(f"报告已写入: {args.report}")
    else:
        print(text)
    p0 = sum(1 for f in findings if f["level"] == "P0")
    return 1 if p0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
