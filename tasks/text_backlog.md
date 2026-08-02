# Interview Text MVP — Complete Atomic Backlog

## Purpose

本文件预先定义从当前状态到文字端面试封板的全部剩余原子任务。正式状态仍以 `docs/03_development/TASKS.md` 为准；DeepSeek 只能执行 `tasks/todo.md` 当前激活的任务，不能因为本文件已经写好就越级执行。

## Scope Lock

包含：项目、大纲、角色圣经、Showrunner、Writer Brief、剧本、QC、Story Memory、跨集连续性、文字评测、一句话第一集、日志、API 文档、CI 和面试交付。

排除：Storyboard、Shot、图片、视频、音频、字幕、FFmpeg、前端、部署、用户、支付、微服务、队列和商业能力。

## Shared Definition of Done

每个任务都必须：

1. 满足前置依赖，只修改任务包白名单。
2. 为每次真实请求使用唯一 Request ID；不得用重复调用刷成功结果。
3. 不记录密钥、完整 Prompt 或完整模型响应。
4. 追加 execution log；由 Codex 独立验收后才能更新 TASKS。
5. 代码任务运行定向测试和全部 pytest；Phase 关闭任务同步实际 API/架构/数据/工作流文档。

## S3-7B — Project 16 Complete Season

| ID | Depends | Type / likely scope | Acceptance | Verification |
|---|---|---|---|---|
| S3-7B-A1 | S3-7A | Read-only baseline; see current queue file | Episodes 1–2 stable, episode 2 obligations and episodes 3–5 baseline recorded | DB fingerprint + diff check |
| S3-7B-A2 | A1 | Real API: episode 3; see current queue file | Brief/script succeed, QC pass, Script/Memory atomic, history stable | Request audit + hashes |
| S3-7B-A2-R1 | A2 attempt 1 blocked | Read-only root-cause analysis | Classify attempt-by-attempt issue migration and identify exact responsible layer without another LLM call | Brief/QC/log/code evidence matrix |
| S3-7B-A2-R2 | R1 requires change + Codex approval | Minimal Prompt/feedback fix + tests, S | Fix only the proven failure mechanism without weakening QC or continuity gates | Focused RED→GREEN + full pytest |
| S3-7B-A2-R3 | R1 no-code decision or R2 accepted | One real episode-3 retry | Exactly one request; QC pass and atomic save, or auditable failure with no formal-data pollution | Request ID + DB/log audit |
| S3-7B-A3 | A2 | Real API: episode 4; see current queue file | Same gate for episode 4 and episode 3 contract | Request audit + hashes |
| S3-7B-A3-R1 | A3 attempt 1 blocked | Codex read-only diagnosis | Prove carried-forward Prompt contract is missing while backend validation is correct | Prompt/validator/log evidence |
| S3-7B-A3-R2 | R1 | QC Prompt + prompt test, S | Require carried-forward items to be re-emitted as current-episode obligations with valid evidence | Prompt test + full pytest |
| S3-7B-A3-R3 | R2 accepted | One real episode-4 retry | Exactly one request; QC pass and atomic save, or auditable safe failure | Request ID + DB/log audit |
| S3-7B-A3-R4 | R3 safe 502 | QC retry feedback + tests, M | Convert grounding issues into explicit, ID/path-specific correction instructions without weakening validation | Captured second-prompt tests + full pytest |
| S3-7B-A3-R5 | R4 accepted | Final real episode-4 retry | One request only; pass atomically or stop Prompt iteration for architecture review | Request ID + DB/log audit |
| S3-7B-E4-BriefFix-R1 | User-authorized EP4 fix review | Brief Prompt narrowing + test, S | Contract actions cannot be banned, while character knowledge, secret reveal and future-resolution boundaries remain allowed | Prompt behavior assertions + full pytest |
| S3-7B-A4 | A3 | Real API: episode 5; see current queue file | Same gate for episode 5 and episode 4 contract | Request audit + hashes |
| S3-7B-A5 | A4 | Read-only checkpoint; see current queue file | Episodes 1–5 contiguous and obligations carried/resolved | Full pytest + continuity matrix |
| S3-7B-B1 | S3-7B-A accepted | Read-only DB/log audit; execution log only | Episodes 1–5 stable; episode 5 obligations due in episode 6; episodes 6–8 baseline hashed | SQLite read-only fingerprint + diff check |
| S3-7B-B2 | B1 | Real API: episode 6 brief/script | HTTP 200, QC pass, approved Memory exact, episode 1–5 unchanged | Request log chain + before/after hashes |
| S3-7B-B3 | B2 | Real API: episode 7 brief/script | Same gate for episode 7; episode 6 contract resolved | Request log chain + atomicity audit |
| S3-7B-B4 | B3 | Real API: episode 8 brief/script | Same gate for episode 8; history unchanged | Request log chain + atomicity audit |
| S3-7B-B5 | B4 | Read-only checkpoint | Episodes 1–8 contiguous; obligations 1→8 carried/resolved; no hidden retries | Full pytest + continuity matrix |
| S3-7B-C1 | B5 accepted | Read-only DB/log audit | Episode 8 obligations due in 9; episodes 9–10 baseline recorded | Stable JSON hashes + DB fingerprint |
| S3-7B-C2 | C1 | Real API: episode 9 brief/script | HTTP 200, QC pass, episode 8 contract resolved, episode 10 obligations prepared | Request audit + atomicity hashes |
| S3-7B-C3 | C2 | Real API: episode 10 brief/script | HTTP 200, QC pass, final Script/Memory atomic, earlier episodes unchanged | Request audit + terminal-state checks |
| S3-7B-C4 | C3 | Read-only terminal audit | Episode 10 fulfills Episode Plan ending, has no episode 11 obligation, all due obligations resolved | Exact IDs/paths + ending evidence audit |
| S3-7B-D1 | C4 accepted | Export under `eval_outputs/` | One readable project-16 Markdown contains idea, outline, characters, Showrunner and scripts 1–10 | Parser/read-back check; no secrets |
| S3-7B-D2 | D1 | Export under `eval_outputs/` | Memory/QC/continuity matrix and Request ID index cover episodes 1–10 | Counts and IDs reconcile with DB/log |
| S3-7B-D3 | D2 | Read-only Phase close | All ten episodes structurally valid; all tests pass; artifacts indexed | Full pytest + diff check + Codex review |

Real generation rule for B2–B4 and C2–C3: generate Brief only when absent, then send exactly one script request with `use_showrunner_brief=true`, `run_showrunner_qc=true`, `max_revision_attempts=2`. Any non-200 stops the batch after atomicity evidence is collected.

## S3-7C — Three Latest Full-Season Evaluations

| ID | Depends | Type / likely scope | Acceptance | Verification |
|---|---|---|---|---|
| S3-7C-P1 | S3-7B | Evaluation spec/docs | Freeze three ideas, DeepSeek model, 10 episodes, 90 seconds, QC/revision settings, output paths and stop rules | Spec review; no LLM call |
| S3-7C-A1 | P1 | Real setup APIs: revenge | New project has 10-episode outline, complete characters, Showrunner State and stable hashes | API statuses + DB parseability + logs |
| S3-7C-A2 | A1 | Real APIs: revenge episodes 1–5 | Each episode has Brief, HTTP 200 Script, pass QC, qc_approved Memory and resolved incoming contract | Per-episode IDs + midpoint matrix |
| S3-7C-A3 | A2 | Real APIs: revenge episodes 6–10 | Ten contiguous episodes; episode 10 closes plan and creates no next obligation | Terminal audit + full pytest |
| S3-7C-A4 | A3 | Export: revenge | Genre Markdown, structured JSON and request-log index are complete and readable | Artifact parser/count checks |
| S3-7C-B1 | A4 accepted | Real setup APIs: romance | New project has 10-episode outline, complete characters, Showrunner State and stable hashes | API statuses + DB parseability + logs |
| S3-7C-B2 | B1 | Real APIs: romance episodes 1–5 | Each episode has Brief, HTTP 200 Script, pass QC, qc_approved Memory and resolved incoming contract | Per-episode IDs + midpoint matrix |
| S3-7C-B3 | B2 | Real APIs: romance episodes 6–10 | Ten contiguous episodes; episode 10 closes plan and creates no next obligation | Terminal audit + full pytest |
| S3-7C-B4 | B3 | Export: romance | Genre Markdown, structured JSON and request-log index are complete and readable | Artifact parser/count checks |
| S3-7C-C1 | B4 accepted | Real setup APIs: mystery | New project has 10-episode outline, complete characters, Showrunner State and stable hashes | API statuses + DB parseability + logs |
| S3-7C-C2 | C1 | Real APIs: mystery episodes 1–5 | Each episode has Brief, HTTP 200 Script, pass QC, qc_approved Memory and resolved incoming contract | Per-episode IDs + midpoint matrix |
| S3-7C-C3 | C2 | Real APIs: mystery episodes 6–10 | Ten contiguous episodes; episode 10 closes plan and creates no next obligation | Terminal audit + full pytest |
| S3-7C-C4 | C3 | Export: mystery | Genre Markdown, structured JSON and request-log index are complete and readable | Artifact parser/count checks |
| S3-7C-D | A4, B4, C4 | Aggregate export | One index links all three projects and reconciles 30 scripts, Memories and QC reports | 30/30 presence check; no quality scoring yet |

Failure policy: stop the current genre on the first failed checkpoint, preserve all evidence, and do not start the next genre until Codex decides whether the failure is infrastructure, schema, continuity or content quality.

## S3-7D — Fixed Quality Gate

| ID | Depends | Type / likely scope | Acceptance | Verification |
|---|---|---|---|---|
| S3-7D-A1 | S3-7C | Scoring spec | Freeze 100-point rubric, evidence citation format and fatal-error definitions before scoring | Rubric totals exactly 100 |
| S3-7D-A2 | A1 | Read-only scoring: revenge | Score all seven dimensions with episode/scene evidence; do not alter output | Score arithmetic + evidence references |
| S3-7D-A3 | A2 | Read-only scoring: romance | Same fixed rubric and evidence standard | Score arithmetic + evidence references |
| S3-7D-A4 | A3 | Read-only scoring: mystery | Same fixed rubric and evidence standard | Score arithmetic + evidence references |
| S3-7D-B1 | A4 | Aggregate report | Calculate average/minimum, verify each episode-10 ending and list fatal errors separately | Independent recalculation |
| S3-7D-B2 | B1 if failed | Planning only | Create the smallest repair task tied to failed dimensions/evidence; no generic Prompt rewrite | Codex approval before implementation |
| S3-7D-C | B1 pass or repaired re-score | Gate decision | Average ≥80, every project ≥75, no fatal continuity/character/fact error | Signed-off score index + artifact hashes |

Fixed rubric: outline execution 20, character consistency 20, cross-episode continuity 20, conflict/pacing 15, opening/ending hooks 10, dialogue 10, format/shootability 5.

## S3-8 — One-Idea-to-Approved-Episode-1 API

| ID | Depends | Type / likely scope | Acceptance | Verification |
|---|---|---|---|---|
| S3-8-A1 | S3-7D | API contract docs | Define one request, success response, stage result and normalized 4xx/5xx errors | API design review; no code |
| S3-8-A2 | A1 | Idempotency contract docs | Define idempotency key, repeat behavior, safe retry boundary and partial-state policy | State-transition examples reviewed |
| S3-8-A3 | A1 | Outline GET contract | Define formal read endpoint matching stored outline without regeneration | Contract aligns with existing response schema |
| S3-8-B1 | A1–A2 | Schema tests + schemas, S | Strict input/output/stage schemas reject unknown or invalid fields | Schema unit tests RED→GREEN |
| S3-8-B2 | B1 | Orchestrator service tests/service, M | Reuse existing project→outline→characters→showrunner→brief→script/QC services; no duplicated Agent logic | Fake-service order and failure tests |
| S3-8-B3 | B2 | API endpoint + tests, S | Single versioned endpoint exposes orchestration and Request ID | API success/error contract tests |
| S3-8-B4 | A3 | Outline GET endpoint + tests, S | Existing outline returns 200; missing project/outline returns documented errors; no LLM call | API tests + OpenAPI check |
| S3-8-C1 | B3–B4 | Fake Provider E2E tests, M | One idea produces project, outline, characters, Showrunner, Brief, approved script, pass QC and Memory | Deterministic end-to-end test |
| S3-8-C2 | C1 | Failure/idempotency tests, M | Every stage failure is identified; no draft fact enters formal Memory; duplicate key does not duplicate project/work | Fault-injection matrix |
| S3-8-C3 | C1 | Logging tests, S | All stages share Request ID; safe metadata present; secrets/prompt/output absent | JSONL assertions |
| S3-8-D1 | C1–C3 | One real LLM demonstration | One authorized request completes or produces auditable safe failure without repeat trial | Request ID + DB/log audit |
| S3-8-D2 | D1 | Docs/Phase close | API, architecture, data model, Prompt index and workflow reflect only implemented behavior | Full pytest + docs/OpenAPI review |

MVP limits: synchronous first-episode orchestration only; no full-season one-click, queue, Redis, worker, progress websocket, user system or frontend.

## S3-9 — Interview Delivery

| ID | Depends | Type / likely scope | Acceptance | Verification |
|---|---|---|---|---|
| S3-9-A1 | S3-8 | GitHub Actions workflow, S | Clean runner installs and runs all pytest on push/PR | GitHub Actions green |
| S3-9-A2 | A1 | CI audit | CI needs no real API key; failure output is actionable; caching optional | Run/failure evidence |
| S3-9-B1 | A1 | README | Five-minute setup, configuration, Fake mode and troubleshooting are reproducible | Follow steps from clean shell |
| S3-9-B2 | B1 | README/docs | Three-minute demo, text architecture diagram, Showrunner/Memory/QC decisions and limits are clear | Fresh-reader review |
| S3-9-C1 | S3-8-D1 | Demo artifacts | Stable idea, Fake output, real-success artifact index and commands are present | Artifact links/read-back |
| S3-9-C2 | S3-7D-C | Evaluation artifacts | Three-season scores, Request ID sample and supported/unsupported capability matrix are present | Index completeness check |
| S3-9-D1 | B2 | Read-only redundancy inventory | Classify every candidate as active, compatibility, dev-only, frozen-video or removable | Reference/search evidence |
| S3-9-D2 | D1 approved | Minimal cleanup, task-sized | Remove only proven unused text-backend material; preserve compatibility and frozen video code | Targeted + full pytest |
| S3-9-E1 | C2/D2 | Security/repo audit | No secrets, `.env`, runtime DB/log or unintended generated prose tracked | Git history/status and secret scan |
| S3-9-E2 | E1 | Fresh-clone verification | Install, full pytest and Fake one-idea demo work from a new clone using docs only | Recorded exact commands/results |
| S3-9-F1 | E2 | Final docs/state audit | API.md matches OpenAPI; TASKS and backlog reflect reality; working tree scope understood | Diff/docs/state review |
| S3-9-F2 | F1 | Git release | Logical commits pushed; CI green; interview text MVP tag created | Remote commit/tag verification |
| S3-9-F3 | F2 | Handoff report | Completed features, known limits, demo steps and non-text future work documented | User/Codex sign-off |

## Final Text-Only Exit Criteria

- One sentence can produce an approved first episode through one backend API.
- Three current-model genres produce 30 contiguous scripts with formal Memory and QC evidence.
- Average score ≥80, minimum ≥75, no fatal character/fact/continuity error.
- Full pytest and CI pass without real credentials.
- A fresh clone can run the Fake demo from README in five minutes.
- Storyboard/video/audio/frontend remain explicitly out of scope and unstarted.
