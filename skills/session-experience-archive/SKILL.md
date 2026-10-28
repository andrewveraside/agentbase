---
name: session-experience-archive
description: 把一次会话/任务压缩成"经验贴"，或把长期项目沉淀成可持续更新的"项目经验"，以 Markdown 在线文档存入资料库的「历史项目经验」目录；并负责在项目有新进展时更新同一篇文档。当用户说"压缩对话""形成经验贴/经验帖""把这次的经验存下来""归档到资料库-项目历史经验""沉淀项目经验""更新项目经验""项目有进展了更新一下"时使用。触发词：经验贴、经验帖、压缩对话、会话总结归档、项目历史经验、历史项目经验、沉淀经验、经验md存入资料库、项目经验更新、更新经验贴、更新项目经验。
agent_created: true
---

# 经验归档（→ 资料库「历史项目经验」）

把会话或项目的可复用结论压缩成 Markdown 在线文档存入资料库；并在项目取得后续进展时**更新同一篇文档**。

## 触发时机（AT 选定的轻量方案，2026-09-21）

**不设定时自动化。** 由我在**一轮实质性工作收尾时**自评是否够格归档，够格则在回复**最末**用一句话提议，**绝不擅自写入**。

够格判据（满足任一即算）：
1. 踩到非显而易见的问题并定位到根因
2. 产出可复用的流程 / 命令 / 判据
3. 长期项目取得阶段性进展
4. 建立或修改了长期约定、规则或架构
5. 环境发生有长期影响的变更

不够格：纯查询、单步操作、已有文档已覆盖且无增量。

提议话术（放回复最末，不打断主交付，不用 emoji）：
- 新主题 →「这次的过程可以归档成经验贴，要我存进「历史项目经验」吗？」
- 已有文档 →「X 项目有进展，要我更新那篇项目经验吗？」

**已有同主题文档时提议"更新"而非新建**，避免产生近似重复。

## 目标位置（固定）

| 项 | 值 |
|---|---|
| 空间 spaceId | `ncPjTWNvCd0SM5BxxUc8rv`（**个人空间**，`category=personal`，owner） |
| 父节点 parentId | `PJEkIthkOUn04r88SIRHZP`（文件夹「**历史项目经验**」，`kind=folder`） |

> 用户口语可能说成"项目历史经验"，实际目录名是「历史项目经验」——以实际存在的节点为准，不要另建同名目录。

## 两种文档类型（命名约定，务必区分）

| 类型 | 标题格式 | 特征 | 更新策略 |
|---|---|---|---|
| **会话经验** | `会话经验 · YYYY-MM-DD｜主题` | 一次性总结；跨天写 `A~B` | 一般不再更新，有新发现另开一篇 |
| **项目经验** | `项目经验 · <项目名>` | **标题不含日期**，长期存在 | **每次阶段性进展必须更新原文档** |

**项目经验为什么不带日期**：它需要被稳定定位并持续更新；标题带日期会不断变化、把同一个项目碎成多篇。

### 项目经验文档的必备结构
1. 标题正下方一行状态声明：

   `> 状态：进行中（截至 YYYY-MM-DD）。后续每次取得阶段性进展，请更新本文并在文末「更新记录」追加一条。`
2. 正文按主题分节：速览 / 事实矩阵 / 风险清单 / 待办 · 下次接续 / 方法论沉淀 / 产出物位置
3. **文末必须有「更新记录」表格**：

   `| 日期 | 更新内容 |`

## 前置

1. 运行环境鉴定：`python <library>/runtime_context.py` → `mode`
2. `mode=client` 须换票：`ToolSearch({"tool_names":["connect_open_platform"]})` → `DeferExecuteTool({"toolName":"connect_open_platform","params":{"skill_id":"library"}})`，把 token 经 stdin 首行传入并带 `--token-stdin`
3. 脚本根目录：`<library>` = `E:\GAME1\workboddy\WorkBuddy\resources\app.asar.unpacked\resources\plugins\workbuddy-builtin\skills\library`
   Python 用托管版本 `C:\Users\23171\.workbuddy\binaries\python\versions\3.13.12\python.exe`（`python3` 不在 PATH）

## 写入是否需确认

按 `<library>/mutation.md`：目标为 **personal 空间** 且用户已明确给出名称与位置 → **原始请求即构成提交授权，直接提交，不必二次确认**。仅当目标落在 team 空间时才需展示方案并等待确认。

> **例外（硬规则）：带 `nodeBlockId` 的全文覆盖不适用上述豁免——无论 personal 还是 team，都必须先确认。**

## 执行步骤 A：新建经验贴

1. **写本地 md 草稿**（先落地，便于审阅与重试）。文件名建议与标题一致。
2. **本地校验**（不发网络请求、不需 token）：
   ```
   python <library>/doc/create_doc.py --dry-run --title "<标题>" --content-file "<md路径>"
   ```
   看到 `content=ok` 且 `contentBytes` 合理再继续。
3. **正式创建**：
   ```
   printf '%s' "<token>" | python <library>/doc/create_doc.py --token-stdin \
     --title "<标题>" \
     --space-id "ncPjTWNvCd0SM5BxxUc8rv" \
     --parent-id "PJEkIthkOUn04r88SIRHZP" \
     --content-file "<md路径>"
   ```
4. **读 `KS_DOC_CREATE` 行的第 5、6 列**（failedCount / fatalCount）。**任一 > 0 → 文档已建但内容可能不完整，必须提示用户打开核对。**
5. **只读验收**：`space.workspace.node-info --node-id <nodeBlockId>`，确认 `kind=doc`、`parentId` 等于目标父节点、`spaceId` 正确。
6. **回执**：原样透传 `KS_USER_REPLY` 整行正文，**不要自行拼接链接、改写文案或补写内部 ID**。

## 执行步骤 B：更新已有经验贴（项目有新进展时）

1. **定位节点**（拿 nodeId）：
   ```
   space_api.py space.workspace.list-node --token-stdin \
     --space-id ncPjTWNvCd0SM5BxxUc8rv --parent-node-id PJEkIthkOUn04r88SIRHZP
   ```
   按**精确标题**匹配已有文档；同名多个时先向用户消歧。
2. **必读最新正文**（拿 blockId，**禁止猜测、禁止跨文档复用**）：
   ```
   printf '%s' "<token>" | python <library>/doc/get_doc_reviews.py --page-id <nodeId> --token-stdin
   ```
   > 两个脚本的 `--help` **都不显示 `--token-stdin`**，但实际都支持；缺 token 会返回 `AUTH_REQUIRED`——**连 `--dry-run` 也需要 token**（实测 2026-09-21）。
3. **构造 actions**（格式见 `<library>/doc/tasks/`：文字块走 `text_block_edit.md`，表格走 `table_edit.md`，复杂组件走 `complex_edit.md`）
4. **本地校验**（同样必须带 token）：
   ```
   printf '%s' "<token>" | python <library>/doc/submit_doc_edit.py --page-id <nodeId> \
     --actions-file "<actions.json>" --dry-run --token-stdin
   ```
   看到 `actions=ok` 再提交。
5. **提交**：
   ```
   printf '%s' "<token>" | python <library>/doc/submit_doc_edit.py --token-stdin \
     --page-id <nodeId> --actions-file "<actions.json>"
   ```
   成功标志：`KS_DOC_EDIT_SUBMIT` 行返回 anchorBlockId + affectedBlockIds，`KS_USER_REPLY` 说明"已即时落入正文"。
6. **只读验收**（重新 `get_doc_reviews.py` 确认新增内容在、原有内容未被破坏）+ 原样透传 `KS_USER_REPLY`。

### actions 构造要点（纯追加场景）

- 插入位置用 `insert_after` + 锚点块 id（如某节最后一个块），**新块不带 id**（由服务端分配）。
- **多个块写在同一条 action 的 `content` 里，块间以空行分隔**——不要拆成多条 action。
- 追加只影响新增块时，走**直接编辑**即可；一旦要改动/删除已有块，转 `submit_review_edit.py` 审阅式。

### 更新时的模式选择

| 变更性质 | 走哪条 |
|---|---|
| 只追加（新增章节、文末「更新记录」加一行） | 直接编辑 `submit_doc_edit.py`（免审阅） |
| 改 / 删 / 替换 / 移动已有内容 | 审阅式编辑 `submit_review_edit.py` |
| 模式或范围无法从上下文确定 | 先问用户 |

### 更新内容的三条铁律

1. **追加优于重写**——保留历史判断的演进痕迹。
2. **文末「更新记录」必加一行**（日期 + 一句话说明改了什么）。
3. **新旧结论冲突时，明确标注"原结论已更新"并说明原因，不要直接删掉旧内容**——否则下次会重犯同样的判断。

## 内容规范

- 正文**只写 Markdown**；禁止混入 `<Paragraph>`、`<Callout>`、`<Table>`、`<Mark>` 等组件。表格用 GFM，Mermaid 用 fenced code，引用用 `>`。
- 长中文内容一律走 `--content-file`，避免 shell 引号与编码问题。
- 经验贴建议结构（按内容取舍，不硬套）：
  1. **结论速览**——最可复用的 5～6 条，放最前
  2. **能力/事实矩阵**——用表格压缩对照关系
  3. **踩过的坑与规律**——写"判据"而非"故事"
  4. **可复用流程**——带确切命令或步骤
  5. **待验证 / 待办**
  6. **一句话总结**
- **只写可复用结论，不写流水账。** 判断标准：换一个人、换一个项目，这段话还用得上吗？
- **脱敏**：经验贴会长期留存与检索。**已公开披露的信息可入库**；未公开的交易细节、审计工作底稿内容、个人身份信息、凭据与内部 ID **不入库**。

## 已知边界

- 资料库**文件夹节点没有删除 API**（Doc block 删除按"修改"走）。建错目录只能改名或移动，谨慎建新目录。
- **没有历史版本列表或恢复 API**——更新是单向的，覆盖前务必备份本地 md。
- Doc 带 `node-block-id` 的**全量覆盖**须先确认（personal 与 team 都要），不能走免确认分支。
- 本机 bash 环境不完整：`ls`/`head`/`tail`/`dirname`/`rm` 均不可用；删除文件用托管 Python 的 `os.remove`。
- 脚本 stdout 为空或返回 JSON error → 视为失败，不要盲目重试。

## 组件化编辑的六个坑（2026-09-23 实测，都踩过）

1. **`--actions-file` 的顶层必须是裸 JSON 数组** `[{...},{...}]`。
   写成 `{"actions":[...]}` 会报「actions 必须是非空数组」。
2. **直接编辑（`submit_doc_edit.py`）实际改不了已有块**。
   `update` 会被服务端拒绝：`code=11607 … Update new_content 缺少 <Mark ar="insert|delete|format"> diff 标识`；
   而直接编辑模式又明令禁止 `Mark ar`。两者互斥 →
   **改已有块只有两条路**：① 审阅式 `submit_review_edit.py`（带 `--summary` + 末尾正好一条 `card_op`）；
   ② 整块 `delete` + `insert_*`。⚠️ 第 ② 条对**表格 cell 内的段落走不通**（cell 不能作为 action 目标，
   删掉里面唯一的段落就没有锚点了）——这类只能走审阅式。
3. **`content/new_content` 的文本会被服务端做一次 Markdown 转义**（关键坑）：
   反斜杠→`\\`、下划线→`\_`、星号→`\*`，`&` 与 `<` 前会多出一个反斜杠；
   **行内代码（反引号）内的内容不受影响**（对照另一篇老文档：`` `KUAICHA_API_KEY` ``、
   `` `C:\Users\<u>\Desk` `` 都保持原样）。
   → 写 **Windows 路径、`file_path` 这类标识符、含 `_`/`*` 的文件名**，一律放进反引号；
   → 纯中文里表达「小于」写「早于/小于」，连接符写「、」而不是 `&`。
   本次因此有 7 个段落中招（`file\_path`、`E:\\workbuddy\\…`、`\*\*只\*\*`），只能再补一次审阅式修正。
4. **写 `<Table>` 不要带 `readonly` / `id` 属性**：它们只出现在回读结果里。
   给已有表加一行 → 用 `table_edit_helper.py insert_row`（或手写）生成**完整的新 `<Table>`**（不含 id），
   再对旧表 `delete` + 对表前那条 Heading `insert_after`。
5. **`get_doc_reviews.py` 的 stdout 是「正文在前、`KS_DOC_REVIEWS` 行在最后」**，
   用 `split('KS_DOC_REVIEWS')[0]` 取正文，别用 `[-1]`。
6. **同一位置插入多个顶层块 → 合并在一条 insert action 的 `content` 里**，块间空行分隔。

## 长期文档的追加清单（本项目照此执行）

1. 先 `space.workspace.list-node` 看有没有同主题文档；有则**更新**，不新建。
2. 回读最新正文（拿块 id）→ 本地备份成 md。
3. 追加内容用 `insert_after(锚点=新内容要落在其后的那个块)`；
   新章节放在倒数第二节与「更新记录」之间，避免打乱既有编号。
4. 「更新记录」表加一行（本行属 append，可走直接编辑）。
5. 提交后**回读验收**：标题序列、旧章节是否仍在、新内容是否被转义（见坑 3）。
6. 原样透传 `KS_USER_REPLY`，不要自拼链接。
