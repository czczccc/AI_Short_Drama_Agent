"""Run text-side API evaluation cases and export human-readable artifacts.

This script intentionally calls the FastAPI app through TestClient instead of
service functions, so requests still pass through API routing, middleware,
validation, persistence, LLM provider wiring, and structured request logging.
"""

from __future__ import annotations

import argparse
import json
import multiprocessing
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.api.main import app

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except AttributeError:
    pass


IDEAS: dict[str, dict[str, str]] = {
    "revenge": {
        "genre": "复仇/逆袭",
        "name": "文字端评测-复仇逆袭",
        "idea": "一个被公司开除的程序员发现老板窃取了他的AI成果",
    },
    "romance": {
        "genre": "甜宠/爱情",
        "name": "文字端评测-甜宠爱情",
        "idea": "一个冷面女总裁为了挽救家族公司，被迫和总是迟到的天才甜品师假装订婚，却发现他正是三年前雨夜救过她的人",
    },
    "suspense": {
        "genre": "悬疑/反转",
        "name": "文字端评测-悬疑反转",
        "idea": "一个深夜电台主播收到自称来自明天的听众来电，对方准确预告了城市里即将发生的失踪案，而主播发现每个受害者都和自己遗忘的童年有关",
    },
}


def _perform_request_for_eval(
    method: str,
    path: str,
    request_id: str,
    json_body: dict[str, Any] | None,
    queue: multiprocessing.Queue,
) -> None:
    started_at = time.perf_counter()
    try:
        with TestClient(app) as client:
            response = client.request(
                method,
                path,
                headers={"X-Request-ID": request_id},
                json=json_body,
            )
        elapsed_ms = round((time.perf_counter() - started_at) * 1000)
        try:
            response_body = response.json()
        except ValueError:
            response_body = response.text
        queue.put(
            {
                "request_id": request_id,
                "method": method,
                "path": path,
                "request_body": json_body,
                "status_code": response.status_code,
                "elapsed_ms": elapsed_ms,
                "response_headers": {
                    "x-request-id": response.headers.get("x-request-id"),
                    "content-type": response.headers.get("content-type"),
                },
                "response_body": response_body,
            }
        )
    except Exception as exc:
        elapsed_ms = round((time.perf_counter() - started_at) * 1000)
        queue.put(
            {
                "request_id": request_id,
                "method": method,
                "path": path,
                "request_body": json_body,
                "status_code": None,
                "elapsed_ms": elapsed_ms,
                "response_headers": {},
                "response_body": {
                    "error_type": type(exc).__name__,
                    "detail": str(exc),
                },
            }
        )


class EvalRunner:
    def __init__(
        self,
        output_dir: Path,
        request_timeout_seconds: int | None = 180,
        max_revision_attempts: int = 1,
    ):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.request_logs: list[dict[str, Any]] = []
        self.request_timeout_seconds = request_timeout_seconds
        self.max_revision_attempts = max_revision_attempts

    def request(
        self,
        client: TestClient,
        method: str,
        path: str,
        *,
        request_id: str,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if self.request_timeout_seconds is None:
            started_at = time.perf_counter()
            response = client.request(
                method,
                path,
                headers={"X-Request-ID": request_id},
                json=json_body,
            )
            elapsed_ms = round((time.perf_counter() - started_at) * 1000)
            try:
                response_body = response.json()
            except ValueError:
                response_body = response.text
            log = {
                "request_id": request_id,
                "method": method,
                "path": path,
                "request_body": json_body,
                "status_code": response.status_code,
                "elapsed_ms": elapsed_ms,
                "response_headers": {
                    "x-request-id": response.headers.get("x-request-id"),
                    "content-type": response.headers.get("content-type"),
                },
                "response_body": response_body,
            }
        else:
            log = self._request_with_hard_timeout(
                method=method,
                path=path,
                request_id=request_id,
                json_body=json_body,
            )
        self.request_logs.append(log)
        print(
            f"{log['status_code']} {method} {path} "
            f"{log['elapsed_ms']}ms request_id={request_id}",
            flush=True,
        )
        if log["status_code"] is None:
            raise RuntimeError(
                f"Request failed before HTTP response: {method} {path} "
                f"body={log['response_body']}"
            )
        if log["status_code"] >= 400:
            raise RuntimeError(
                f"Request failed: {method} {path} "
                f"status={log['status_code']} body={log['response_body']}"
            )
        return log["response_body"]

    def _request_with_hard_timeout(
        self,
        *,
        method: str,
        path: str,
        request_id: str,
        json_body: dict[str, Any] | None,
    ) -> dict[str, Any]:
        started_at = time.perf_counter()
        context = multiprocessing.get_context("spawn")
        queue = context.Queue()
        process = context.Process(
            target=_perform_request_for_eval,
            args=(method, path, request_id, json_body, queue),
        )
        process.start()
        process.join(self.request_timeout_seconds)
        if process.is_alive():
            process.terminate()
            process.join(10)
            return {
                "request_id": request_id,
                "method": method,
                "path": path,
                "request_body": json_body,
                "status_code": None,
                "elapsed_ms": round((time.perf_counter() - started_at) * 1000),
                "response_headers": {},
                "response_body": {
                    "error_type": "RequestTimeout",
                    "detail": (
                        "Request exceeded hard timeout of "
                        f"{self.request_timeout_seconds} seconds"
                    ),
                },
            }
        if queue.empty():
            return {
                "request_id": request_id,
                "method": method,
                "path": path,
                "request_body": json_body,
                "status_code": None,
                "elapsed_ms": round((time.perf_counter() - started_at) * 1000),
                "response_headers": {},
                "response_body": {
                    "error_type": "RequestWorkerNoResult",
                    "detail": "Request worker exited without returning a result",
                },
            }
        return queue.get()

    def run_case(
        self,
        case_key: str,
        *,
        resume_project_id: int | None = None,
        reuse_showrunner: bool = False,
        regenerate_characters: bool = False,
        start_episode: int = 1,
    ) -> dict[str, Any]:
        case = IDEAS[case_key]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        slug = f"{timestamp}_{case_key}"
        project_name = f"{case['name']}-{timestamp}"
        prefix = f"text-eval-{timestamp}-{case_key}"
        existing_scripts: dict[str, Any] = {}

        with TestClient(app) as client:
            if resume_project_id is None:
                created = self.request(
                    client,
                    "POST",
                    "/api/v1/projects",
                    request_id=f"{prefix}-create-project",
                    json_body={"name": project_name},
                )
                project_id = created["id"]

                outline = self.request(
                    client,
                    "POST",
                    f"/api/v1/projects/{project_id}/outline",
                    request_id=f"{prefix}-outline",
                    json_body={"idea": case["idea"], "episode_count": 10},
                )
                characters = self.request(
                    client,
                    "POST",
                    f"/api/v1/projects/{project_id}/characters/generate",
                    request_id=f"{prefix}-characters",
                    json_body={},
                )
            else:
                project_id = resume_project_id
                state = self.request(
                    client,
                    "GET",
                    f"/dev/projects/{project_id}/state",
                    request_id=f"{prefix}-resume-state",
                )
                project_name = state["project"]["name"]
                existing_scripts = {
                    str(number): {
                        "project_id": project_id,
                        "episode_number": int(number),
                        "status": state["project"]["status"],
                        "script": script,
                    }
                    for number, script in state["scripts"].items()
                }
                outline = {
                    "project_id": project_id,
                    "status": state["project"]["status"],
                    "outline": state["outline"],
                }
                if regenerate_characters:
                    characters = self.request(
                        client,
                        "POST",
                        f"/api/v1/projects/{project_id}/characters/generate",
                        request_id=f"{prefix}-characters",
                        json_body={},
                    )
                else:
                    characters = {
                        "project_id": project_id,
                        "status": state["project"]["status"],
                        "characters": state["characters"],
                    }
            showrunner = self.request(
                client,
                "GET" if reuse_showrunner else "POST",
                f"/api/v1/projects/{project_id}/showrunner",
                request_id=(
                    f"{prefix}-showrunner-existing"
                    if reuse_showrunner
                    else f"{prefix}-showrunner"
                ),
                json_body=None if reuse_showrunner else {},
            )

            writer_briefs: dict[str, Any] = {}
            scripts: dict[str, Any] = existing_scripts
            qc_reports: dict[str, Any] = {}
            for episode_number in range(start_episode, 6):
                brief = self.request(
                    client,
                    "POST",
                    f"/api/v1/projects/{project_id}/episodes/{episode_number}/writer-brief",
                    request_id=f"{prefix}-brief-e{episode_number}",
                    json_body={
                        "target_duration_seconds": 90,
                        "force_regenerate": False,
                    },
                )
                writer_briefs[str(episode_number)] = brief
                script = self.request(
                    client,
                    "POST",
                    f"/api/v1/projects/{project_id}/episodes/{episode_number}/script",
                    request_id=f"{prefix}-script-e{episode_number}",
                    json_body={
                        "target_duration_seconds": 90,
                        "use_showrunner_brief": True,
                        "run_showrunner_qc": True,
                        "max_revision_attempts": self.max_revision_attempts,
                    },
                )
                scripts[str(episode_number)] = script
                qc_reports[str(episode_number)] = self.request(
                    client,
                    "GET",
                    (
                        f"/api/v1/projects/{project_id}/episodes/"
                        f"{episode_number}/showrunner-qc"
                    ),
                    request_id=f"{prefix}-qc-e{episode_number}",
                )

        result = {
            "case_key": case_key,
            "genre": case["genre"],
            "idea": case["idea"],
            "project_id": project_id,
            "project_name": project_name,
            "outline": outline,
            "characters": characters,
            "showrunner": showrunner,
            "writer_briefs": writer_briefs,
            "scripts": scripts,
            "qc_reports": qc_reports,
        }
        self.write_case_markdown(slug, result)
        self.write_request_logs()
        return result

    def write_case_markdown(self, slug: str, result: dict[str, Any]) -> None:
        path = self.output_dir / f"{slug}.md"
        outline = result["outline"]["outline"]
        characters = result["characters"]["characters"]
        scripts = result["scripts"]
        qc_reports = result["qc_reports"]

        parts: list[str] = [
            f"# {result['genre']}文字端评测",
            "",
            "## 基本信息",
            "",
            f"- Project ID：`{result['project_id']}`",
            f"- Project Name：`{result['project_name']}`",
            f"- Idea：{result['idea']}",
            "",
            "## 故事大纲（阅读版）",
            "",
            f"- 标题：{outline.get('title')}",
            f"- 类型：{outline.get('genre')}",
            f"- 基调：{outline.get('tone')}",
            f"- Logline：{outline.get('logline')}",
            f"- 世界设定：{outline.get('world_setting')}",
            f"- 核心冲突：{outline.get('core_conflict')}",
            "",
            "### 10 集大纲",
            "",
        ]
        for episode in outline.get("episodes", []):
            parts.extend(
                [
                    f"#### 第 {episode.get('episode_number')} 集：{episode.get('title')}",
                    "",
                    f"- Summary：{episode.get('summary')}",
                    f"- Main Conflict：{episode.get('main_conflict')}",
                    f"- Ending Hook：{episode.get('ending_hook')}",
                    "",
                ]
            )

        parts.extend(["## 角色设定", ""])
        for character_id, character in characters.items():
            parts.extend(
                [
                    f"### {character.get('name')}（`{character_id}`）",
                    "",
                    f"- 角色定位：{character.get('role')}",
                    f"- 年龄：{character.get('age')}",
                    f"- 背景：{character.get('background')}",
                    f"- 外貌：{character.get('appearance')}",
                    f"- 性格：{character.get('personality')}",
                    f"- 动机：{character.get('motivation')}",
                    f"- 恐惧：{character.get('fear')}",
                    f"- 秘密：{character.get('secret')}",
                    f"- 说话风格：{character.get('speech_style')}",
                    f"- 角色弧光：{character.get('character_arc')}",
                    "",
                ]
            )

        parts.extend(["## 第 1-5 集剧本原文", ""])
        for episode_number in range(1, 6):
            script = scripts[str(episode_number)]["script"]
            report = qc_reports.get(str(episode_number), {}).get("report")
            parts.extend(
                [
                    f"## 第 {episode_number} 集：{script.get('title')}",
                    "",
                    f"- 目标时长：{script.get('duration_seconds')} 秒",
                    f"- 本集目标：{script.get('episode_goal')}",
                    f"- 开场钩子：{script.get('opening_hook')}",
                    f"- 结尾钩子：{script.get('ending_hook')}",
                    (
                        f"- Showrunner QC：{report.get('status')}｜"
                        f"{report.get('summary')}"
                        if report
                        else "- Showrunner QC：无报告"
                    ),
                    "",
                ]
            )
            for scene in script.get("scenes", []):
                parts.extend(
                    [
                        f"### 场 {scene.get('scene_number')}：{scene.get('location')} / {scene.get('time_of_day')}",
                        "",
                        f"- 出场角色：{', '.join(scene.get('characters', []))}",
                        f"- 场景目标：{scene.get('scene_goal')}",
                        f"- 动作：{scene.get('action')}",
                        "",
                        "台词：",
                        "",
                    ]
                )
                for dialogue in scene.get("dialogues", []):
                    parts.append(
                        f"- **{dialogue.get('character_name')}**"
                        f"（{dialogue.get('emotion')}）：{dialogue.get('line')}"
                        f"｜动作：{dialogue.get('action_note')}"
                    )
                parts.extend(["", f"- 转场：{scene.get('transition')}", ""])

        parts.extend(
            [
                "## 原始 JSON 附录",
                "",
                "### Outline JSON",
                "",
                "```json",
                json.dumps(outline, ensure_ascii=False, indent=2),
                "```",
                "",
                "### Characters JSON",
                "",
                "```json",
                json.dumps(characters, ensure_ascii=False, indent=2),
                "```",
                "",
                "### Scripts JSON",
                "",
                "```json",
                json.dumps(scripts, ensure_ascii=False, indent=2),
                "```",
                "",
                "### Showrunner QC JSON",
                "",
                "```json",
                json.dumps(qc_reports, ensure_ascii=False, indent=2),
                "```",
                "",
            ]
        )
        path.write_text("\n".join(parts), encoding="utf-8")
        print(f"WROTE {path}", flush=True)

    def write_request_logs(self) -> None:
        json_path = self.output_dir / "request_response_logs.json"
        md_path = self.output_dir / "request_response_logs.md"
        json_path.write_text(
            json.dumps(self.request_logs, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        rows = [
            "# Request / Response Logs",
            "",
            "| # | status | elapsed_ms | method | path | x-request-id |",
            "|---:|---:|---:|---|---|---|",
        ]
        for index, item in enumerate(self.request_logs, start=1):
            rows.append(
                f"| {index} | {item['status_code']} | {item['elapsed_ms']} | "
                f"{item['method']} | `{item['path']}` | "
                f"`{item['response_headers'].get('x-request-id')}` |"
            )
        rows.extend(
            [
                "",
                "完整请求体和响应体见 `request_response_logs.json`。",
                "",
            ]
        )
        md_path.write_text("\n".join(rows), encoding="utf-8")
        print(f"WROTE {json_path}", flush=True)
        print(f"WROTE {md_path}", flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--case",
        choices=[*IDEAS.keys(), "all"],
        default="revenge",
        help="Evaluation case to run.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory. Defaults to eval_outputs/text_eval_<timestamp>.",
    )
    parser.add_argument(
        "--resume-project-id",
        type=int,
        default=None,
        help="Resume from an existing project that already has outline and characters.",
    )
    parser.add_argument(
        "--request-timeout-seconds",
        type=int,
        default=0,
        help=(
            "Experimental hard timeout for each API request. "
            "Default 0 disables it because Windows subprocess TestClient can hang."
        ),
    )
    parser.add_argument(
        "--reuse-showrunner",
        action="store_true",
        help="Reuse saved Showrunner State when resuming an existing project.",
    )
    parser.add_argument(
        "--regenerate-characters",
        action="store_true",
        help="Regenerate characters from the saved outline when resuming.",
    )
    parser.add_argument(
        "--start-episode",
        type=int,
        choices=range(1, 6),
        default=1,
        help="First episode to generate (1-5). Use with resume to continue a run.",
    )
    parser.add_argument(
        "--max-revision-attempts",
        type=int,
        choices=range(0, 3),
        default=1,
        help="Maximum Writer revisions after Showrunner QC blocks a draft.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = (
        Path(args.output_dir)
        if args.output_dir
        else Path("eval_outputs") / f"text_eval_{timestamp}"
    )
    runner = EvalRunner(
        output_dir,
        request_timeout_seconds=(
            None if args.request_timeout_seconds <= 0 else args.request_timeout_seconds
        ),
        max_revision_attempts=args.max_revision_attempts,
    )
    case_keys = list(IDEAS) if args.case == "all" else [args.case]
    if args.resume_project_id is not None and len(case_keys) != 1:
        raise ValueError("--resume-project-id can only be used with one case.")
    if args.reuse_showrunner and args.resume_project_id is None:
        raise ValueError("--reuse-showrunner requires --resume-project-id.")
    if args.regenerate_characters and args.resume_project_id is None:
        raise ValueError("--regenerate-characters requires --resume-project-id.")
    if args.reuse_showrunner and args.regenerate_characters:
        raise ValueError(
            "--reuse-showrunner cannot be combined with --regenerate-characters."
        )
    if args.start_episode > 1 and args.resume_project_id is None:
        raise ValueError("--start-episode > 1 requires --resume-project-id.")
    for case_key in case_keys:
        print(f"RUNNING {case_key}: {IDEAS[case_key]['idea']}", flush=True)
        try:
            runner.run_case(
                case_key,
                resume_project_id=args.resume_project_id,
                reuse_showrunner=args.reuse_showrunner,
                regenerate_characters=args.regenerate_characters,
                start_episode=args.start_episode,
            )
        except Exception as exc:
            runner.write_request_logs()
            status_path = output_dir / "RUN_STATUS.md"
            status_path.write_text(
                "\n".join(
                    [
                        "# Text Eval Run Status",
                        "",
                        "## 结论",
                        "",
                        f"`{case_key}` case 未完整跑通。",
                        "",
                        "## 失败原因",
                        "",
                        f"- Error Type：`{type(exc).__name__}`",
                        f"- Detail：{exc}",
                        "",
                        "## 请求日志",
                        "",
                        "- `request_response_logs.md`",
                        "- `request_response_logs.json`",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            print(f"WROTE {status_path}", flush=True)
            raise
    print(f"DONE output_dir={output_dir}", flush=True)


if __name__ == "__main__":
    main()
