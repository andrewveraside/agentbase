---
name: xlsx-sheet-split
description: 把一个多 sheet 的 xlsx 按工作表拆成多个独立工作簿。用于「拆 sheet」「按工作表拆分」「每个 sheet 单独存一个文件」「把明细表分给各分公司/事业部」「排除某个表不拆」。采用 ZIP/XML 层级无损切分，不丢格式。
agent_created: true
---

# xlsx 按 sheet 拆分

## 何时用
用户要把一个多工作表的工作簿拆成多个单表文件。审计场景典型：应收账款/收入明细表按分公司、事业部拆开分别发出；函证清单按主体分拆。

## 为什么不用 openpyxl 重写
`load_workbook` + `save` 会丢条件格式的部分内容、数据透视表、图片、切片器等，且几十万行时极慢。
**正确做法**：xlsx 本质是 ZIP。把目标 sheet 的 `xl/worksheets/sheetN.xml` 字节原样搬到新 zip，只重写四份元数据：

| 必须重写的文件 | 改什么 |
|---|---|
| `xl/workbook.xml` | `<sheets>` 只留目标表，`sheetId=1`，`r:id=rId1`；`<definedNames>` 留全局的 + `localSheetId` 命中该表的（序号归 0） |
| `xl/_rels/workbook.xml.rels` | 删掉其他 worksheet 关系，保留 theme/styles/sharedStrings |
| `[Content_Types].xml` | 删掉其他 `worksheets/sheetN.xml` 的 Override |
| `docProps/app.xml` | 删掉 `HeadingPairs` / `TitlesOfParts`（留着会因数量不符触发 Excel 修复提示） |

`sharedStrings.xml` / `styles.xml` 整份复制，索引不变，天然安全。代价是每个输出文件多带约一份 styles+strings 的体积，可接受。

## 执行
```bash
python split_by_sheet.py <源文件.xlsx> [输出目录] [--exclude 表1 表2 ...] [--include-hidden] [--prefix 前缀]
```
- 输出目录省略时，默认在源文件同级建 `拆分结果/`。
- 常见用法：`python split_by_sheet.py 明细.xlsx 拆分结果 --exclude 目录 汇总`
- 依赖仅标准库。Windows 上 Python 请用托管的 venv：
  `C:\Users\23171\.workbuddy\binaries\python\envs\default\Scripts\python.exe`

## 坑（都踩过）
1. **不要在同一个 `ZipFile` 对象上边遍历边 `read()` 再写另一个 zip**，会报 `BadZipFile: Bad magic number for file header`。把源整个读成 `bytes`，每次 sources_Sheet 前用 `fresh_zip(raw)` 新建一个 ZipFile。
2. workbook/rels/CT 三棵 ElementTree 会被**就地修改**，每张表导出前必须重新 `ET.fromstring` 解析。
3. 隐藏的空残留表（如 `Sheet1`）默认跳过；确实要就用 `--include-hidden`。判断依据是 xml 里没有 `<row`。
4. `localSheetId` 是**表的序号（0 起）**，不是 sheetId。目标表变成唯一表后要改成 0。

## 结果要验证
拆完必须校验，不能只看没报错。用 openpyxl 逐个打开，比对：
- sheet 数 == 1 且表名与源一致
- `calculate_dimension()` 与源同表一致
- 前若干行值与源一致
- 顺带记录合并单元格数、冻结窗格、自动筛选、自定义列宽数，确认格式要素还在

可参考本 skill 同目录下 split_by_sheet.py 的 `split()` 返回值自行扩展。

## 环境备注
PowerShell 调用 stdout 有时被平台吞掉。稳妥做法是脚本把结果写进文件再读；或 `cmd *>&1 | Set-Content -Path xxx.txt -Encoding UTF8`。
