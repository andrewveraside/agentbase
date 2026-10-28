# AgentBase · 四端 agent 共用行为底座

一套让多个 AI 编程 agent 在**同一台机器**上行为一致的规范底座：一份 `AGENTS.md`、一个 skills 共享库、一个把规范注入各宿主的 sync 脚本。

## 为什么需要它

同一个人往往同时用 3~4 个 agent 宿主（DeepSeek Harness / WorkBuddy / CodeBuddy / ZCode 等）。各自有自己的人设文件，导致：

- 同一条"省 token 的读法"要在四个地方各改一遍，改漏一处就行为不一致；
- 某个宿主里踩到的坑，换一个宿主又要重新踩；
- skills 目录各存一份副本，版本漂移。

AgentBase 的做法是**一个唯一源 + 注入副本**：规范只写 `AGENTS.md`，由 `base_sync.py` 把它注入各宿主的配置文件，用 `<!-- AGENTBASE:BEGIN -->` / `<!-- AGENTBASE:END -->` 标记块包裹，**replace 而非叠加**，标记块以外的宿主个性化内容（人设、IDENTITY）不受影响。

## 目录

```
AGENTS.md        # 唯一源：回答方式、工作纪律、保密、技能与工具等通用规范
base_sync.py     # 注入脚本：把 AGENTS.md 的标记块写进各宿主
skills/          # 共享技能库（每个子目录一个 skill，含 SKILL.md）
tools/           # 配套工具（如知识库 MCP server）
```

## 注入到哪

`base_sync.py` 默认注入到以下位置（路径按各宿主的默认 `~` 位置，可按需修改）：

| 宿主 | 目标文件 |
|---|---|
| WorkBuddy | `~/.workbuddy/SOUL.md` |
| DeepSeek Harness | `~/.dsh/AGENTS.md` |
| CodeBuddy | `~/.codebuddy/AGENTS.md` |
| CodeBuddy | `~/.codebuddy/CODEBUDDY.md` |

## 用法

```bash
# 1. 编辑 AGENTS.md（规范只写这里）
# 2. 备份现有配置（建议，脚本本身不备份）
# 3. 注入
python base_sync.py
```

**重要约定**：新规则只能加在 `AGENTS.md` 的 `## 1.` 到 `## 5.` 之间。脚本实现上会重写从 `## 6.` 开始的段落，写在其后的文字会在下次 sync 时被截掉。

## 设计取舍

- **标记块而非全文覆盖**：宿主自己的 SOUL / IDENTITY 里有富有个性的内容（语气、角色），不应被通用规范冲掉。
- **不做符号链接**：Windows 上目录联接容易被备份/同步工具破坏，副本 + 一个 sync 命令更可控。
- **技能用目录名做身份**：`skills/<name>/SKILL.md`，前端按目录名列出，不用维护索引文件。
- **规范可迁移**：文中出现某个宿主独有的工具名时，读者按"读文件 / 写文件 / 执行命令 / 搜索"等价替换，不做宿主绑定。

## License

MIT
