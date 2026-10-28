---
name: git-guardrails
description: Guard rails for destructive git operations. Use before or during any history-rewriting or destructive git command (force push, reset --hard, clean, branch -D, checkout -- ., restore), when the user asks to protect a branch, or after an agent has already force-pushed by mistake. Provides an agent-enforced pre-flight protocol plus deterministic Husky hooks.
description_zh: "危险 git 操作（强制推送、reset --hard、clean、branch -D）前的防护：先确认再执行，并用 Husky 做确定性拦截"
description_en: "Guard rails for destructive git operations: confirm before history-rewriting commands, enforce deterministically with Husky"
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
# Git Guardrails

Original upstream skill installed a Claude Code `PreToolUse` hook to block dangerous git commands. **CodeBuddy has no equivalent command-interception hook**, so this version splits the guarantee in two:

1. **Agent-side protocol** — you enforce it yourself, every time, before running a destructive command.
2. **Repo-side hooks** — Husky runs on git events, independent of any agent or IDE. This is the deterministic half.

## The denylist

Never run these without an explicit, informed go-ahead in the current conversation:

```
git push --force            git push -f
git reset --hard
git clean -fd                git clean -fdx
git branch -D                git checkout -- .
git restore .               git stash drop / clear
git rebase (onto a shared branch)
git filter-branch            git reflog expire --expire=now --all
```

## Pre-flight protocol

Before any command on the list:

1. **Name the blast radius out loud** in one sentence: what work becomes unreachable, and who else is affected if this is a shared branch.
2. **Check whether it is recoverable.** Uncommitted changes are the usual casualty. Run `git status --porcelain` first; if it is non-empty and the user has not acknowledged it, stop and ask.
3. **Check whether it is published.** If the branch has an upstream or the commits exist on a remote, treat the operation as one-way.
4. **Propose the safe alternative** when one exists: `git stash` or a WIP commit instead of `reset --hard`; `--force-with-lease` instead of `--force`; a throwaway branch instead of `clean -fd`.
5. **Only then run it**, using the narrowest form of the command that does the job (`git clean -n` first to preview).

A one-word "yes" to a question you did not ask does not count as informed consent. If the user has already said "do it" in this conversation, that counts.

## When you have already broken something

If a destructive command has already run:

1. Stop. Do not run any further git command.
2. Report plainly what was lost and what still exists (`git reflog`, `git fsck --lost-found`, dangling commits).
3. Recover from the reflog rather than improvising: `git reset --hard <sha>` on a local branch, or `git cherry-pick` onto a fresh branch.
4. Do not run `git reflog expire` or `gc` until recovery is confirmed — those destroy the evidence.

## Deterministic half: Husky hooks

Set these up with the `setup-pre-commit` skill (CodeBuddy ships it), then add the guards:

- **`pre-commit`** — lint-staged (format + lint on staged files) and typecheck. A commit that fails checks never gets created.
- **`pre-push`** — reject pushes to `main`/`master` and reject `--force` unless the branch is explicitly allow-listed. This is the one that actually prevents the accident, because it does not depend on the agent's judgement.

Keep the pre-push hook small, and state in its failure message how to bypass it deliberately (e.g. `HUSKY=0 git push`) so the user is never stuck.

## What this skill does not do

- It does not protect against a user running the command themselves in their own terminal.
- It does not stop an IDE's built-in VCS UI from force-pushing; tell the user to check their IDE's git settings for "force push" defaults.
- It does not replace a remote-side protection rule (GitHub branch protection / rulesets). Recommend setting one when the repo is on a remote.

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