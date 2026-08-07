"""批量生成整季短剧：从一句话创意到 N 集完整剧本。

用法（需先启动后端服务）：
    python tools/generate_season.py --idea "一句话创意" --episodes 10 [--name 项目名] [--retry 2]

流程：创建项目 → 大纲 → 角色圣经 → Showrunner State → 逐集（Writer Brief + 剧本 + QC）
自动重试：每集脚本失败时自动重试（默认 1 次）；QC 409 时按 retry 次数重生成。

退出码：0 = 全部成功；1 = 有失败集（已记录到汇总）。
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except AttributeError:
    pass

DEFAULT_BASE_URL = "http://127.0.0.1:8000"


def _call(base_url: str, method: str, path: str, body=None, timeout: int = 900):
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    req = urllib.request.Request(base_url + path, data=data, method=method)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8")), time.time() - t0
    except urllib.error.HTTPError as exc:
        try:
            detail = json.loads(exc.read().decode("utf-8"))
        except Exception:
            detail = str(exc)
        return exc.code, detail, time.time() - t0


def _gen(base_url: str, path: str, body, label: str) -> bool:
    status, resp, dt = _call(base_url, "POST", path, body)
    ok = status < 300
    print(f"  [{label}] HTTP {status} ({dt:.0f}s){'' if ok else ' -> ' + json.dumps(resp, ensure_ascii=False)[:300]}")
    return ok


def _health(base_url: str) -> bool:
    try:
        status, resp, _ = _call(base_url, "GET", "/api/v1/health", timeout=5)
        return status == 200 and resp.get("status") == "ok"
    except Exception:
        return False


def run_season(
    idea: str,
    episode_count: int,
    name: str | None = None,
    retry: int = 1,
    base_url: str = DEFAULT_BASE_URL,
    project_id: int | None = None,
    start_episode: int = 1,
    max_revision_attempts: int = 2,
) -> int:
    if episode_count < 10:
        print(f"错误：episode_count 最小为 10（当前 {episode_count}），项目是固定 10 集短剧设计。")
        return 2
    if not _health(base_url):
        print(f"错误：后端服务不可达（{base_url}）。请先启动 uvicorn app.api.main:app。")
        return 2

    if project_id is None:
        status, resp, dt = _call(base_url, "POST", "/api/v1/projects", {"name": name or f"短剧 {datetime.now():%H%M%S}"})
        if status >= 300:
            print("创建项目失败:", json.dumps(resp, ensure_ascii=False)[:300])
            return 2
        project_id = resp["id"]
        print(f"创建项目 id={project_id} ({resp['name']})")

        # 前置三步（大纲/角色/State）——仅新建项目时执行
        print(f"生成大纲（{episode_count} 集）...")
        if not _gen(base_url, f"/api/v1/projects/{project_id}/outline",
                    {"idea": idea, "episode_count": episode_count}, "OUTLINE"):
            return 2
        print("生成角色圣经...")
        if not _gen(base_url, f"/api/v1/projects/{project_id}/characters/generate", {}, "CHARACTERS"):
            return 2
        print("生成 Showrunner State...")
        if not _gen(base_url, f"/api/v1/projects/{project_id}/showrunner", {}, "SHOWRUNNER"):
            return 2
    else:
        print(f"使用已有项目 id={project_id}（跳过创建与前两步前置，仅续跑剧集）")

    # 逐集生成
    failed: list[int] = []
    existing_episodes: set[int] = set()
    if project_id is not None:
        status, resp, _ = _call(base_url, "GET", f"/api/v1/projects/{project_id}")
        if status < 300 and resp.get("scripts_json"):
            existing_episodes = {
                int(key) for key in json.loads(resp["scripts_json"]).keys()
            }
    for episode in range(start_episode, episode_count + 1):
        if episode in existing_episodes:
            print(f"--- 第 {episode} 集 ---（已存在，跳过）")
            continue
        print(f"--- 第 {episode} 集 ---")
        ok = False
        for attempt in range(retry + 1):
            if _gen(base_url, f"/api/v1/projects/{project_id}/episodes/{episode}/writer-brief",
                    {}, f"BRIEF ep{episode}") and _gen(
                base_url, f"/api/v1/projects/{project_id}/episodes/{episode}/script",
                {"use_showrunner_brief": True, "run_showrunner_qc": True,
                 "max_revision_attempts": max_revision_attempts},
                f"SCRIPT ep{episode}",
            ):
                ok = True
                break
            if attempt < retry:
                print(f"  ep{episode} 第 {attempt + 1} 次失败，重试...")
        if not ok:
            failed.append(episode)
            print(f"  !! ep{episode} 重试耗尽，失败")

    print()
    print("=" * 50)
    print(f"项目 id={project_id} 结果：{episode_count - len(failed)}/{episode_count} 集成功")
    if failed:
        print(f"失败集：{failed}（可用 --project-id {project_id} --start-episode {failed[0]} 续跑）")
        return 1
    print("全部成功")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="批量生成整季短剧")
    parser.add_argument("--idea", required=True, help="一句话故事创意")
    parser.add_argument("--episodes", type=int, default=10, help="集数（固定 10 集短剧，最小 10）")
    parser.add_argument("--name", help="项目名（默认自动生成）")
    parser.add_argument("--retry", type=int, default=1, help="每集失败重试次数（默认 1）")
    parser.add_argument("--max-revision-attempts", type=int, default=2, help="QC 返修上限（默认 2，0-2）")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="后端地址")
    parser.add_argument("--project-id", type=int, help="续跑：指定已有项目 id（跳过创建与前置）")
    parser.add_argument("--start-episode", type=int, default=1, help="从第几集开始（配合 --project-id 续跑）")
    args = parser.parse_args()

    return run_season(
        idea=args.idea,
        episode_count=args.episodes,
        name=args.name,
        retry=args.retry,
        base_url=args.base_url,
        project_id=args.project_id,
        start_episode=args.start_episode,
        max_revision_attempts=args.max_revision_attempts,
    )


if __name__ == "__main__":
    raise SystemExit(main())
