# -*- coding: utf-8 -*-
"""base sync：读取 D:\\AgentBase\\AGENTS.md 唯一源，注入四家入口文件（5 处，含 wb 的
user-*-personal/SOUL.md）。第 6 节由本文件 NEW6 重写：源文件「## 6.」之后的内容会被
替换，新规则只能加在第 1–5 节。幂等。"""
import glob, os, re

HOME = os.path.expanduser("~")
C = r"D:\AgentBase\AGENTS.md"
BEGIN = "<!-- AGENTBASE:BEGIN 由 D:\\AgentBase\\AGENTS.md 生成，勿手改；改请改源文件后再跑 sync -->"
END = "<!-- AGENTBASE:END -->"

NEW6 = """## 6. 四家是谁（互相知道存在即可）

| 名字 | 宿主 | 定位 |
|---|---|---|
| **wb** | WorkBuddy | 领域判断（审计 / 外贸）、connector 独有能力（iFinD、金山文档、企微、网盘、云 DB）、cb 的既有派单方 |
| **cb** | CodeBuddy | 编程执行，偏代码实现与 IDE 内操作 |
| **dsh** | DeepSeek Harness | 基础设施、脚本化执行与核对；可在内部开 AgentTeams（成员都属 dsh，指挥不了 wb/cb） |
| **zcode** | ZCode（智谱 GLM，2026-10-24 入伙） | 编程与通用任务执行；派单边界待 AT 指定 |

原则：

- 四家**互相知道对方存在**，但**互不指挥**。wb 与 cb 的协作方式（brief → result）保持不变，dsh / zcode 不介入、不派单。
- 谁都不替对方承诺，也不替对方调用其独有能力。
- 跨家协作只走两条路：共享记忆（`D:\\ScopeRecall\\shared`）或用户转发；不假设能直接调用对方。
- 事实记忆共享；人设与规范各自加载本文件。

## 7. 底座自身的维护

- 唯一源：`D:\\AgentBase\\AGENTS.md`。改动后跑 sync 重注入，不要直接改各家的副本。
- 副本都带 `AGENTBASE:BEGIN / END` 标记，replace 而非叠加。
- 技能唯一源：`D:\\AgentBase\\skills`（各家目录为联接）；旧副本归档在 `D:\\AgentBase\\archive`。
"""

def upsert(path, body):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    old = open(path, encoding="utf-8", errors="ignore").read() if os.path.isfile(path) else ""
    pat = re.compile(re.escape(BEGIN) + r".*?" + re.escape(END) + r"\n?", re.S)
    new = pat.sub(lambda m: body.strip() + "\n", old) if pat.search(old) else (old.rstrip() + "\n" + body)
    if new != old:
        open(path, "w", encoding="utf-8").write(new)
        return "updated"
    return "unchanged"

def main():
    s = open(C, encoding="utf-8").read()
    i = s.index("## 6.")
    s = s[:i] + NEW6
    open(C, "w", encoding="utf-8").write(s)
    print("canonical updated,", len(s.encode("utf-8")), "bytes")

    block = "\n" + BEGIN + "\n" + s + "\n" + END + "\n"
    targets = {
        "wb/SOUL.md":            os.path.join(HOME, ".workbuddy", "SOUL.md"),
        "dsh/AGENTS.md":         os.path.join(HOME, ".dsh", "AGENTS.md"),
        "cb/AGENTS.md":          os.path.join(HOME, ".codebuddy", "AGENTS.md"),
        "cb/CODEBUDDY.md":       os.path.join(HOME, ".codebuddy", "CODEBUDDY.md"),
        "zcode/AGENTS.md":       os.path.join(HOME, ".zcode", "AGENTS.md"),
    }
    # wb 会话实际加载 user-*-personal/SOUL.md（根 SOUL.md 的块一直没生效），两处都注入
    for p in sorted(glob.glob(os.path.join(HOME, ".workbuddy", "user-*-personal", "SOUL.md"))):
        targets[f"wb/personal/{os.path.basename(os.path.dirname(p))}"] = p
    for k, p in targets.items():
        print(f"  {k}: {upsert(p, block)}")

if __name__ == "__main__":
    main()
