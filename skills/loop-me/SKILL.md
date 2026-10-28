---
name: loop-me
description: Grill me about specs for the workflows I want to build, within this workspace.
version: 1.0.0-codebuddy
homepage: https://github.com/mattpocock/skills
---


## 跨宿主适配（AgentBase）

本技能在 WorkBuddy / CodeBuddy / DSH 三处共用。文中若出现某一宿主专用的工具名，按当前环境等价替换：

| 文中写法 | 你的环境里应理解为 |
|---|---|
| `Read` | 读取文件（用你所在宿主的读文件工具） |
| `Write` / `Edit` | 写入或修改文件 |
| `Bash` | 执行 shell 命令 |
| `Grep` / `Glob` | 搜索文件内容 / 按模式找文件 |
| `Task` | 起子代理（环境不支持则串行完成） |
| `WebFetch` | 抓取网页 |

技能名同理：当前宿主没有的技能，跳过并在结果中说明，不要假装调用过。
Run a stateful `grilling` skill session whose only output is **workflow** specs. Use the grilling discipline (relentless, a round of questions at a time, a recommended answer attached to each) aimed at the vocabulary and goal below. Create, edit, and delete specs as the grilling resolves things.

## The loop lens

A **loop** is a recurring pattern in the user's life: their career, their week, their morning, a single repeated activity. Picturing a life as loops within loops reveals how predictable its activities really are, which is what makes them worth **delegating**. Use the lens to find loops worth specifying, and propose ones the user hasn't noticed.

A **workflow** is the spec of one loop, made real. You run a workflow on a loop: the loop is its running instantiation. Workflows live in `workflows/*.md` and are the source of truth.

## Vocabulary

A shared language, reached for only when a workflow calls for it: never a checklist. **Mandate nothing structural**: a workflow needs no AI, no checkpoint, and no schedule unless the grilling shows it does.

- **Trigger**: what fires each run, an **event** (a new email, a new issue) or a **schedule** (every morning). Event-triggering is usually the more efficient.
- **Checkpoint**: a human-in-the-loop point where the user is asked to verify or decide. Some workflows have none and run autonomously; some use no AI at all.
- **Push right**: defer the checkpoint as far as it will go. Do maximal work before involving the human, so they are asked once, late, with everything prepared.
- **Brief**: what a checkpoint presents, a tight, decision-ready summary (what was produced, why, and a link down to the asset itself), never the raw output. The user reads a brief, not a draft. Speed of review is imperative.

## Definition of done

A workflow spec is done when an implementer agent could build it without asking a single question. Grill until then; nothing is done while a question remains.

## The workspace

- `workflows/*.md`: one spec per workflow.
- `NOTES.md`: raw notes on the user's world, the tools they use, the channels they process, and their own terminology for both. When it is empty or thin, interview them about their world before specifying anything. Sharpen fuzzy terms into canonical ones as they surface, and record them here.

## CodeBuddy environment notes

Tool mapping for this environment (use these, not Claude Code names):

| Purpose | CodeBuddy tool |
|---|---|
| Load another skill | `use_skill` with `command: "<skill-name>"` |
| Delegate exploration / parallel work | `task` with `subagent_name: "code-explorer"`; multiple named teammates for team mode |
| Ask the user structured questions | `ask_followup_question` |
| Track work | `todo_write` |
| Read / write / edit files | `read_file`, `write_to_file`, `replace_in_file` |
| Search | `search_file`, `search_content`, `list_dir` |
| Shell | `execute_command` (PowerShell on Windows: no `grep`/`cat`/`&&` chaining) |
| Web | `web_search`, `web_fetch` (look them up with `ToolSearch`, then call via `DeferExecuteTool`) |
| Lint / diagnostics | `read_lints` |

- There is no `Task`-style background agent, no `AskUserQuestion`, and no `/clear` or `/compact` command. To free context, start a new session and hand over via the `handoff` skill.
- Project instructions: `CODEBUDDY.md` (or `AGENTS.md` when no `CODEBUDDY.md`). Project rules: `.codebuddy/rules/<name>/RULE.mdc`.
- `gh` / `glab` may not be installed and `git` may be absent. Always probe first with `git --version` / `gh --version`; when unavailable, use the local-markdown tracker (`.scratch/<feature>/issues/`) instead of failing.
- Git-only mechanics (worktrees, integration branches, PR links) degrade to sequential single-branch work when git is unavailable.
- `*.sh` templates in this skill folder are bash. On Windows, port them to PowerShell before use.