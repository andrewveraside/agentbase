---
name: 外贸知识库
description: 查询中国进出口税则（2026）税率、商品归类依据，以及外贸实务法规（关税法、计税价格、出口退免税、3C认证、归类预裁定、减免税）。当用户询问 HS 编码/税则号列对应的税率、某设备应归哪个税号、协定税率、进口环节税、报关归类流程、3C 认证要求、出口退免税、或数据中心设备（服务器/交换机/UPS/空调/柴油发电机等）进口合规问题时使用。触发词：税率、税则、HS编码、税号、归类、报关、进口、出口、退税、免税、3C、CCC、预裁定、协定税率、最惠国税率、服务器、交换机、UPS、精密空调、数据中心进口。
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
# 外贸知识库

本地外贸知识库，位置：`E:\workbuddy\资料库\外贸知识库`

## 何时用这个 Skill

只要问题涉及以下任一项，先读本Skill，不要凭记忆回答税率和税号：

- **查税率**：某 HS 编码的最惠国税率/协定税率/普通税率
- **定归类**：某设备应归哪个税则号列
- **走流程**：报关归类、3C 认证、归类预裁定、减免税适用
- **出口退税**：备案单证、收汇、开票时限
- **数据中心设备进口**：服务器、交换机、存储、UPS、精密空调、冷水机组、柴油发电机、机柜、配电柜

## 快速查询（最常用）

> **⚠️ 本环境（WorkBuddy Bash 沙箱）调用须知**：`PY="..."` / `Q="..."` 这类 **shell 变量赋值会被沙箱拦截**（报 `decisionRecord missing actual resource subject`，关沙箱也无效）。**必须写完整绝对路径直接调用**，不要图省事用变量。

```bash
# 模板：仅替换末尾参数（税号 / --find 关键词 / --ch 章号 / --dc / --stats / --chapters）
"C:/Users/23171/.workbuddy/binaries/python/versions/3.13.12/python.exe" "E:/workbuddy/资料库/外贸知识库/脚本工具/query.py" 84715010
"C:/Users/23171/.workbuddy/binaries/python/versions/3.13.12/python.exe" "E:/workbuddy/资料库/外贸知识库/脚本工具/query.py" 8471
"C:/Users/23171/.workbuddy/binaries/python/versions/3.13.12/python.exe" "E:/workbuddy/资料库/外贸知识库/脚本工具/query.py" --find 变压器
"C:/Users/23171/.workbuddy/binaries/python/versions/3.13.12/python.exe" "E:/workbuddy/资料库/外贸知识库/脚本工具/query.py" --ch 85
"C:/Users/23171/.workbuddy/binaries/python/versions/3.13.12/python.exe" "E:/workbuddy/资料库/外贸知识库/脚本工具/query.py" --chapters
"C:/Users/23171/.workbuddy/binaries/python/versions/3.13.12/python.exe" "E:/workbuddy/资料库/外贸知识库/脚本工具/query.py" --dc
"C:/Users/23171/.workbuddy/binaries/python/versions/3.13.12/python.exe" "E:/workbuddy/资料库/外贸知识库/脚本工具/query.py" --stats
```

## 库结构

```
E:\workbuddy\资料库\外贸知识库\   76 MB
├─ 税率表_按章/               275 份  CSV主数据 + 274 分章 md
├─ 法规实操/17 份  法规原文 + 合规清单
│   ├─ 出口业务增值税消费税政策_财政部税务总局公告2026年第11号.md★上位依据
│   ├─ 3C认证与免办实操.md ／ 归类预裁定办事指南.md
│   ├─ RCEP原产地管理办法_海关总署令255号.md
│   ├─ 213号令_计税价格办法.md ／ 272号令_征税管理办法.md
│   ├─ 进境物品分类与计税价格_公告2024年第175号.md
│   ├─ 保税物流账册核销管理_公告2024年第174号.md
│   ├─ 外汇管理优化贸易外汇业务管理通知.md
│   └─ 数据中心设备进口合规自查清单.md ★四道关卡检查表
├─ 教材/                2 份  进出口报关实务、图解外贸会计实操（38 万字）
├─ ima迁入/              15 份  官方解读与地方口径
├─ 归类依据/               16 份  84/85章注释、归类总规则
├─ 脚本工具/                17 份  查询与维护脚本
├─ 3 份原始 PDF                67 MB（自包含）
├─ README.md
└─ 2026税则知识库_使用手册.md
```

**库内自带原始 PDF，不依赖外部文件即可完整重建。**

---

## 核心工具：`脚本工具/query.py`

不依赖任何服务，纯 CSV 查询，毫秒级。调用同上，**必须用完整路径、禁用 shell 变量赋值**（见上方"快速查询"警告）：
```bash
"C:/Users/23171/.workbuddy/binaries/python/versions/3.13.12/python.exe" "E:/workbuddy/资料库/外贸知识库/脚本工具/query.py" 84715010   # 8位税号精确查
"C:/Users/23171/.workbuddy/binaries/python/versions/3.13.12/python.exe" "E:/workbuddy/资料库/外贸知识库/脚本工具/query.py" 8471        # 4位品目列全部
"C:/Users/23171/.workbuddy/binaries/python/versions/3.13.12/python.exe" "E:/workbuddy/资料库/外贸知识库/脚本工具/query.py" --find 空调  # 品名模糊搜
"C:/Users/23171/.workbuddy/binaries/python/versions/3.13.12/python.exe" "E:/workbuddy/资料库/外贸知识库/脚本工具/query.py" --ch 85       # 第85章全部
"C:/Users/23171/.workbuddy/binaries/python/versions/3.13.12/python.exe" "E:/workbuddy/资料库/外贸知识库/脚本工具/query.py" --dc          # 数据中心设备速查
"C:/Users/23171/.workbuddy/binaries/python/versions/3.13.12/python.exe" "E:/workbuddy/资料库/外贸知识库/脚本工具/query.py" --stats       # 库统计
```

## 标准工作流

### 场景 A：已知税号，查税率
1. 跑 `query.py <税号>`
2. 若需要申报要素或品名细节 → 用 Read 读 `税率表_按章/第XX章_*.md` 对应文件
3. 回答时**必须给出原始 PDF 页码**（`来源页`），便于用户回原税则核对

### 场景 B：只知道设备，要定归类
1. 跑 `query.py --dc` 看该设备对应哪些候选品目
2. 读 `归类依据/` 里对应章注释
3. **必须提示归类风险**：同类设备可能跨品目（如 UPS 在 8504、精密空调在 8415，同为"机房设备"但税号完全不同）
4. **建议申请归类预裁定**（零成本、有效期 3 年、具海关约束力），见 `法规实操/归类预裁定办事指南.md`

### 场景 C：走报关流程
1. 读 `法规实操/数据中心设备进口合规自查清单.md`——四道关卡（归类→3C→税收优惠→原产地）
2. 关键：服务器（8471）与交换机（8517）**分属不同品目，混报必被人工复核**
3. 3C 是真正的门槛（不是关税）——服务器在 CCC 目录第 09 类 0911 项

## 税率字段口径

| 字段 | 含义 |
|---|---|
| 最惠国税率（MFN） | 适用于 WTO 成员等；**数字或空** |
| 从属国附注 | `∆` 表示该税率仅适用于特定受让国，见协定税率栏 |
| 协定税率 | 24 项自贸协定，格式为"国别代码+税率" |
| 特惠税率 | 最不发达国家等，大量为空属正常 |
| 普通税率 | 非协定国适用，阶梯高（14~130） |
| 来源页 | **原始 1492 页 PDF 的真实页码**，可回原 PDF 逐字核对 |

## 重要提醒（每次回答都要把关）

1. **税率仅供查询参考，正式申报以"中国国际贸易单一窗口"（singlewindow.cn）实时查询为准。** 海关对税率有最终解释权。
2. **归类以海关预裁定决定书为最终依据**，本库是参考。
3. **服务器/交换机/存储类 MFN=0 是真实的**（信息技术产品零关税），已回原 PDF 核实，不是错误。
4. **税则逐年更新**（通常次年 1 月 1 日施行）。本库为 2026 年版，若用户处理的是其他年度，需先确认。
5. 涉及"这个税率合不合理""这样报有没有风险"时，**明确区分已核实与需用户确认**，不要替用户下判断。
6. **🚫 关税税率 ≠ 出口退税率（两套口径，严禁混用）**：本库**同时含**两套数据——①关税（`税率表_按章`，MFN/协定/普通）；②**出口退税率**（分组 `出口退税率_2026C`，来源税务总局《出口退税率文库2026C版》税总货劳函〔2026〕214号，2026-09-30，全库 100 篇覆盖全税则）。查退税率优先走该文库（如 8471 退税率=13%，且退税率=征税率、征退差为零）。**关键红线：绝不能拿关税 MFN 充当出口退税率**——例：8471 的 MFN=0 是关税零税率，与其出口退税率 13% 完全两回事；被问「8471 退税率多少」必须答退税率 13%（查文库），不是 MFN=0。

## 库的历史与局限

- 2026 版共 8972 个税目（与官方税目总数一致），数据提取自财政部官网发布的税则 PDF 原文
- MFN 解析率 99.11%，80 条因含`∆` 等符号未能解析为纯数字（已在"从属国附注"列保留原样）
- 协定税率栏是长文本（"东盟AS,智CL,巴PK..."），未做结构化拆解
- 原始 PDF 全文备份在`E:\workbuddy\2026-10-07-17-04-24\ima_src\中华人民共和国进出口税则2026.pdf`（70 MB）

## 维护权与协作边界（2026-10-23 交接 dsh｜权威）

> 本 skill 的**维护权已移交 dsh**，以下边界由 dsh 在 `E:\worcod\dsh@wb-外贸知识库交接回复.md` 中明确，wb 必须照此执行。

- **主库 = DSH 的 waimao-kb MCP**（**现 450 篇 / 8 分组**：dsh 13:50 接手时 350 篇/7 分组，随后补入税务总局《出口退税率文库2026C版》100 篇 → 新增「出口退税率_2026C」分组；另含 dsh 入库的「库地图」）。库体在 `E:\DshData\.dsh\knowledge\knowledge.sqlite`，正文副本 `documents\base-0b76e338\`。调用走 `mcp__waimao-kb__kb_search` / `kb_read` / `kb_groups`（只读）。
- **wb 本地这份 skill 仅作离线兜底**（MCP 不可用时），**不主动补库、不双份维护**——否则与 DSH 库必然漂移。
- **新增资料 / 抓到的新公告 → 落到 `E:\worcod\pending\` 交 dsh 入库**（dsh 走本地 API 入库，保留分组/类型/标签）。**不要直接改 DSH 库**（MCP 只读也改不了）。这是「无需重复维护两份内容」的落地办法。
- **税则版本硬过期**：2026 版 2027-01-01 失效 → 由 dsh 在 12 月起盯「2027 年关税调整方案」，发布后重提取。wb 不自行重提取。
- **dsh 已给 kb_search 加 AND→OR 降级**（多词 AND 零命中自动放宽成 OR，返回首行带降级提示，脚本在 `D:\AgentBase\tools\kb_mcp.py`）。**wb 需重启 WorkBuddy / 重连 MCP 才会加载新版逻辑**；重启后可用 `加工贸易 保税 核销` 验证（应返回 5 篇并带降级提示）。
- **检索习惯**：waimao-kb 是 AND 匹配，多词易零命中；优先用单关键词（如「8471」或「出口退税率」分别查）。降级上线后多词也会兜底，但仍以单关键词最稳。

## 维护

税率更新后需重新提取，脚本在 `脚本工具/`：
```bash
# ⚠️ 必须用完整绝对路径直调（禁用 shell 变量赋值；bare python 不指向托管运行时）
"C:/Users/23171/.workbuddy/binaries/python/versions/3.13.12/python.exe" "E:/workbuddy/资料库/外贸知识库/脚本工具/split_999.py"                       # 从原始PDF 切页段
"C:/Users/23171/.workbuddy/binaries/python/versions/3.13.12/python.exe" "E:/workbuddy/资料库/外贸知识库/脚本工具/extract_v8.py" "<pdf路径>" "1-499"  # ⚠️必须 strategy="lines"，否则约80%列错位
"C:/Users/23171/.workbuddy/binaries/python/versions/3.13.12/python.exe" "E:/workbuddy/资料库/外贸知识库/脚本工具/merge_v8.py"                        # 合并
"C:/Users/23171/.workbuddy/binaries/python/versions/3.13.12/python.exe" "E:/workbuddy/资料库/外贸知识库/脚本工具/fix_pages.py"                      # 页码换算
"C:/Users/23171/.workbuddy/binaries/python/versions/3.13.12/python.exe" "E:/workbuddy/资料库/外贸知识库/脚本工具/split_by_chapter.py"               # 按章拆
"C:/Users/23171/.workbuddy/binaries/python/versions/3.13.12/python.exe" "E:/workbuddy/资料库/外贸知识库/脚本工具/split_big_chapters.py"             # 大章细分

```
---

## 动态更新（让库持续成长）

本库不靠手动"继续迁"维持，而是按以下协议**主动发现缺口并补库**。所有判断以 `_知识地图.json` 为真相源（它不是文档，是脚本扫描校准的覆盖度台账，见 `资料库/外贸知识库/_知识地图.md`）。

### 1. 何时抓（触发条件）
- **缺口触发**：用户问到某主题，先查 `_知识地图.json` 对应域——若 `coverage=partial/missing` 或 `gaps` 命中，且问题超出库内已有内容 → 触发抓取。
- **硬过期触发**：税则每年 1/1 换新。`2026税则` 2027-01-01 失效 → **每年 12 月起专项盯"次年关税调整方案"**，发布即重提取。
- **时效触发**：`_知识地图.json` 中 `staleness[].expire` 临近或已过 → 标红并查补充/废止公告。
- **巡检触发**：第三步「定时巡检自动化」每月跑，主动搜官方源新公告。

### 2. 从哪抓（官方监测源）
优先级从高到低，全部为官方口径（已在 `_知识地图.json` 的 `monitor_sources` 固化）：
1. 国务院关税税则委员会 / 财政部关税司（税则、关税调整方案；栏目 gss.mof.gov.cn/gzdt/zhengcefabu）
2. 海关总署（公告、政策解读）——归类、报关、减免税、AEO、保税
3. 国家税务总局（出口退税政策）
4. 国家外汇管理局（贸易外汇）
5. 中国国际贸易单一窗口（实时税率核对）
6. 市场监管总局（CCC 目录与免办）
7. 商务部（mofcom.gov.cn + 中国自由贸易区服务网 fta.mofcom.gov.cn）——自贸协定谈判/签署/早期收获、出口管制
8. 国家发展改革委——鼓励类产业目录、重大技术装备（减免税专项发文方之一）
9. 工业和信息化部——重大技术装备专项减免税目录

> **⚠️ 源选型门禁（2026-10-08 实战教训，新增）**：优先用权威原文 URL——`gss.mof.gov.cn`、`fta.mofcom.gov.cn`、`customs.gov.cn`、`chinatax.gov.cn`、各部委官网。避开 **JS 重渲染页**（如 `*zwfw.gov.cn` 政务大厅、海外新闻站）——这类 ima 抓取常为空（本次财关税2026-9号源页 `parse_progress` 卡 1%、`file_size=0`）。遇此类源：改取权威转载（财政部/海关/商务部原文或地方政府官网 reprint），或只写本地 md 作为权威交付物，不依赖 ima 解析。

> ima「外贸知识库」已迁完（17 条 + 2 教材），**无删除接口、无需反复迁**；新内容优先走官方源，ima 仅作备份源。

### 3. 怎么抓 → 校验 → 入库（已验证套路）
按来源分流，**严禁凭记忆改税率**：

**A. 税率更新（PDF 重提取）**
```bash
cd "E:/workbuddy/资料库/外贸知识库/脚本工具"
# ⚠️ 本环境 Bash 沙箱禁用 shell 变量赋值，全部用完整 python 路径（不要写 PY=）
"C:/Users/23171/.workbuddy/binaries/python/versions/3.13.12/python.exe" split_999.py                       # 切页段（先更新原始PDF）
"C:/Users/23171/.workbuddy/binaries/python/versions/3.13.12/python.exe" extract_v8.py "<pdf路径>" "1-499"  # ⚠️必须用 strategy="lines"，否则约80%列错位
"C:/Users/23171/.workbuddy/binaries/python/versions/3.13.12/python.exe" merge_v8.py && "C:/Users/23171/.workbuddy/binaries/python/versions/3.13.12/python.exe" fix_pages.py
"C:/Users/23171/.workbuddy/binaries/python/versions/3.13.12/python.exe" split_by_chapter.py && "C:/Users/23171/.workbuddy/binaries/python/versions/3.13.12/python.exe" split_big_chapters.py
"C:/Users/23171/.workbuddy/binaries/python/versions/3.13.12/python.exe" pack.py                            # 重新打包
```
校验：`query.py --stats` 比对条目数；抽样回原 PDF 核对页码；与海关总署公告税目总数交叉验证。

**B. ima / 网页官方解读（md 入库）**
- ima：`mcp__ima-mcp__fetch_media_content` 取正文 → 超长自动落盘 → 读落盘文件 → `parse_ima_dump.py` / `ima_fetch2md.py` 转 md（清微博/微信噪声 + 合并硬换行）→ 存 `法规实操/` 或 `ima迁入/`。
- 网页：`WebFetch` / `WebSearch` 取正文 → 提炼 → 存对应目录，文件名带发布机构与日期。

**C. 入库后解析校验（ima 必做，2026-10-08 新增）**
`import_urls` 后**必须**回查解析状态，不能只看 `ret_code=0`（它只代表入库成功，不代表解析成功）：
- 调 `mcp__ima-mcp__get_knowledge_list`（`limit`≤50）查对应条目的 `media_state` 与 `file_size`：
  - `MEDIA_PARSE_SUCCESS`(2) 且 `file_size>0` → 正常。
  - `MEDIA_PARSING`(3) 卡死 / `MEDIA_PARSE_ERROR` / `MEDIA_PARSE_TIMEOUT` 或 `file_size=0` → **标记该 ima 条目解析失败**。
- 解析失败处理：**本地 md 即权威交付物**，不因此阻塞；**绝不重推**（ima 无删除接口，重推=产生重复条目）；在报告中提示用户——如需 ima 内也有正文，请其在 ima 客户端手动删除该条后，用更好源 URL 重推。
- （可选）**去重预检**：导入前先 `get_knowledge_list` 扫一遍同名 / 同发文字号；已存在且已解析则跳过，避免重复条目。

### 4. 分级处理（置信度）
- **高置信度**（官方公告原文、权威解读、海关总署/财政部文件）→ 直接入库。
- **地方口径 / 报道类** → 先比对知识库是否已有更完整版本；重复则跳过，不重复则存 `ima迁入/` 并标记来源与适用区域。
- **不确定项** → 生成「成长报告」交用户确认，**不自动入库**。
- **本地优先（2026-10-08 改进）**：本地 md 是权威交付物，ima 仅为备份。若 ima 解析失败，以本地 md 为准——不阻塞、不重推（ima 无删除，重推=重复）。

### 5. 入库后必须同步（闭环）
1. 更新 `_知识地图.md` / `_知识地图.json`：对应域 `coverage` / `files` / `verified` / `next_review` / `status`。
2. 更新 `README.md` 目录结构数字（**以知识地图为准，非照抄**）。
3. 重新 `pack.py` 打包。
4. 若由第三步自动化触发，跑完回写 `next_review` 与 `status`。

### 6. 时效规则
- 带"实施 / 废止"日期的文件，到期自动标红，查有无替代文件。
- 每年 1/1 税则换新；12 月起专项巡检。
- 协定税率栏未结构化——新抓的协定细则优先补结构化，不堆长文本。

### 7. 自学习挂钩（查到的新事实 → 自动登记监测事件）★2026-10-08 新增，闭环关键

**问题**：此前发现时效敏感事实（如"中—GCC FTA 尚未生效"）只当一次性结论讲完，未变成"持续监测的事件"——库不会自己长大。

**规则**：在**任何咨询 / 检索 / 回答**过程中，只要发现以下任一类**时效敏感事实**，必须**即时**（当轮、不批处理）登记为 `_知识地图.json` 的 `monitored_events` 一条：
- 协定签署 / 升级 / 早期收获（如中国—GCC FTA 生效）
- 税率 / 税目调整（公告已发、待施行）
- 监管 / 认证要求生效或废止
- 归类裁定 / 预裁定变更
- 其他"当前是一种状态、未来会因某官方动作变成另一种状态"的事实

**登记动作（四步，轻量、不阻塞）**：
1. **查重**：先按 `dedup_key`（如 `china-gcc-fta-in-force`）扫 `monitored_events`；已存在则仅更新 `discovered_at` / `discovered_from`，不重复追加。
2. **追加**：不存在则 Append 一条，必填 `id / topic / type / current_status / discovered_at / discovered_from / trigger / on_trigger / source_hint / dedup_key`。
3. **镜像**：同步写 `_知识地图.md` 的「四、持续监测事件」表。
4. **不阻塞**：登记≠当场改税率/法规——它只把"未来该被盯的事件"挂上钩。

**消费方**：`外贸知识库更新检查` skill 步骤 1 扫描 `monitored_events`，对每条判断 `trigger` 是否已发生；一旦发生，该事件升级为高优先「待更新项」，按 `on_trigger` 执行更新（如补协定税率、标记新伙伴）。——这样"查到事实"与"持续监测"自动咬合，库真正自学习。

**示例（已落地）**：阿联酋光缆经新加坡中转回中国咨询中，发现"中—GCC FTA 未生效"，当轮即登记 `EVT-GCC-FTA`（trigger=海关/商务部公布签署生效；on_trigger=补阿联酋协定税率）。
