---
name: grilling
description: Grill the user relentlessly about a plan, decision, or idea. Use when the user wants to stress-test their thinking, or uses any 'grill' trigger phrases.
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
Interview the user relentlessly until you reach a shared understanding. Map this as a **design tree**: every decision branches into the decisions that hang off it.

Work the tree in **rounds**. The **frontier** is every decision whose prerequisites are already settled: the questions you can ask _now_ without guessing at answers you haven't heard yet. Ask the whole frontier in one round: number each question and give your recommended answer. Then wait for the user's answers before the next round.

Format a round like so:

```
❓ **Q1** - **<question title>**: <question body, might be multiple paragraphs, including multiple choices>

➡️ <your recommended answer>

---

❓ **Q2** - **<question title>**: <question body, might be multiple paragraphs, including multiple choices>

➡️ <your recommended answer>
```

Word each question so "yes" accepts your recommended answer.

Each round the user answers reshapes the tree: settled decisions push the frontier outward and unblock questions that depended on them. Recompute the frontier and ask the next round. A question whose answer depends on another question still open in this round belongs to a _later_ round, not this one.

Finding _facts_ is your job, never the user's. When a frontier question needs a fact from the environment (filesystem, tools, etc.), dispatch a subagent to find it; don't ask the user for anything you could look up yourself. Don't block on it: a running exploration is an unsettled prerequisite, so only the questions downstream of it wait for the subagent to report; ask the rest of the frontier now. The _decisions_ are the user's: put each to them and wait.

The session is done when the frontier is empty: every branch of the design tree visited, nothing left silently assumed. Do not act on it until the user confirms you have reached a shared understanding.

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
