#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""知识库 MCP server（只读，纯标准库，stdio 传输），支持多知识库。

给 WorkBuddy / CodeBuddy / ZCode 等支持 MCP 的宿主提供对 dsh-knowledge 的只读检索。
直接读 knowledge.sqlite 的 FTS 索引，不改库、不开端口、不需要 token、不影响 DSH。

多库支持：kb_search / kb_groups 均接受可选参数 kb（别名或库 id），
默认库为「外贸知识库」，保持对旧调用方的向后兼容。

工具：kb_list / kb_search / kb_read / kb_groups
"""
import json
import sqlite3
import sys

DB_PATH = "E:/DshData/.dsh/knowledge/knowledge.sqlite"

# 库别名表：wiki_v2 建库时可能出现重名（例如两个同名库），别名务必绑 id 不要绑名字
KB_ALIASES = {
    "trade":  "0b76e338-30da-4000-b39a-19488f5c6c0c",   # 外贸知识库
    "finance": "8c730f8b-80c1-4cdd-8931-78a1c584ccc0",  # 财税知识库
}
DEFAULT_KB = "trade"
PROTOCOL = "2025-06-18"

# 旧变量名保留，避免外部脚本 import 时炸
BASE_ID = KB_ALIASES[DEFAULT_KB]

TOOLS = [
    {
        "name": "kb_list",
        "description": "列出本机所有可查的知识库及其条目数。查任何资料前若不确定该查哪个库，先调它。",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "kb_search",
        "description": "检索知识库，返回命中文档的标题、分组、片段和 id，需要全文再调 kb_read。默认查「外贸知识库」（进出口报关、归类、税率表、原产地、退税）；问财税/增值税/企业所得税/出口退税账务/发票/汇兑损益时传 kb=\"finance\" 查「财税知识库」。不确定有哪些库就先调 kb_list。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "检索词，中文即可。多个词用空格分隔，按 AND 匹配。"},
                "kb": {"type": "string", "description": "库别名（trade/finance）或库 id。默认 trade（外贸知识库）。"},
                "limit": {"type": "integer", "description": "返回条数，默认 6，最大 20。"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "kb_read",
        "description": "读取 kb_search 命中的某篇文档全文。引用法规条款、税率表、归类依据时必须用原文，不要凭摘要复述。文档 id 全局唯一，通常不必传 kb；若指定了 kb 则校验文档属于该库。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "description": "kb_search 返回的文档 id。"},
                "kb": {"type": "string", "description": "可选。库别名或库 id；不传则跨库按 id 直取。"},
                "offset": {"type": "integer", "description": "起始字符位置，默认 0。"},
                "max_chars": {"type": "integer", "description": "最多返回字符数，默认 8000，最大 40000。"},
            },
            "required": ["id"],
        },
    },
    {
        "name": "kb_groups",
        "description": "列出某个知识库的分组及各组文档数，用于判断某个问题该查哪一块（如税率表_按章、归类依据、法规实操、教材、ima迁入）。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "kb": {"type": "string", "description": "库别名（trade/finance）或库 id。默认 trade（外贸知识库）。"},
            },
        },
    },
]


def connect():
    return sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True, timeout=10)


def resolve_kb(kb):
    """把 kb 参数解析成 (库id, 库名)。传别名/全 id 均可；不传用默认库。"""
    key = (kb or "").strip()
    if not key:
        key = DEFAULT_KB
    kb_id = KB_ALIASES.get(key.lower(), key)
    conn = connect()
    try:
        row = conn.execute(
            "SELECT name FROM knowledge_bases WHERE id=? LIMIT 1", (kb_id,)
        ).fetchone()
    except sqlite3.OperationalError:
        row = None
    finally:
        conn.close()
    if not row:
        raise ValueError(
            "未知的知识库 %r。可用别名：%s，或先调 kb_list 查看全部库 id。"
            % (key, "、".join(KB_ALIASES))
        )
    return kb_id, row[0]


def kb_list():
    conn = connect()
    try:
        rows = conn.execute(
            """SELECT b.id, b.name, COUNT(e.id)
               FROM knowledge_bases b
               LEFT JOIN knowledge_entries e
                      ON e.knowledge_base_id = b.id AND e.status='active'
               WHERE b.status='active'
               GROUP BY b.id, b.name ORDER BY b.name""",
        ).fetchall()
    finally:
        conn.close()
    # 过滤系统自带的空占位库（id=default），它永远 0 条，列出来只会误导
    rows = [r for r in rows if r[0] != "default" or r[2] > 0]
    if not rows:
        return "本机没有任何知识库。"
    alias_of = {v: k for k, v in KB_ALIASES.items()}
    out = ["本机共 %d 个知识库：" % len(rows)]
    for kid, name, n in rows:
        tag = ("（别名 %s）" % alias_of[kid]) if kid in alias_of else ""
        mark = "  ← 默认" if kid == KB_ALIASES[DEFAULT_KB] else ""
        flag = "  ⚠ 空库" if n == 0 else ""
        out.append("  - %s%s：%d 篇%s%s\n      id：%s" % (name, tag, n, mark, flag, kid))
    out.append("\n检索时把别名或库 id 传给 kb_search 的 kb 参数；不传则查外贸知识库。")
    return "\n".join(out)

def fts_query(text, mode="AND"):
    words = [w for w in text.replace('"', " ").split() if w]
    if not words:
        return None
    return (" " + mode + " ").join('"' + w + '"' for w in words[:8])


def _fts_rows(conn, expr, limit, kb_id):
    try:
        return conn.execute(
            """SELECT e.id, e.title, e.document_group, e.tags_json, e.type,
                      snippet(knowledge_fts, 2, '', '', '…', 20) AS frag
               FROM knowledge_fts f JOIN knowledge_entries e ON e.id = f.knowledge_id
               WHERE knowledge_fts MATCH ? AND e.status='active' AND e.knowledge_base_id=?
               ORDER BY rank LIMIT ?""",
            (expr, kb_id, limit),
        ).fetchall()
    except sqlite3.OperationalError:
        return []


def kb_search(query, limit, kb=None):
    kb_id, kb_name = resolve_kb(kb)
    limit = max(1, min(int(limit or 6), 20))
    conn = connect()
    try:
        expr = fts_query(query)
        words = [w for w in query.replace('"', " ").split() if w][:8]
        rows = []
        relaxed = False
        if expr:
            rows = _fts_rows(conn, expr, limit, kb_id)
            if not rows and " AND " in expr and len(words) > 1:
                # 多词 AND 零命中。不能直接用 FTS 的 OR 结果——FTS5 unicode61 对中文
                # 不分词，整词做 OR 会命中「只含其中一个词」的无关文档（如查
                # 「增值税法 实施条例」命中《企业所得税法实施条例》）。所以 OR 只用来
                # 收候选，再用「逐词 LIKE 全含」二次过滤，过滤后为空才继续走下面的兜底。
                cand = _fts_rows(conn, fts_query(query, "OR"), max(limit * 5, 20), kb_id)
                if cand:
                    ids = [c[0] for c in cand]
                    ph = ",".join("?" * len(ids))
                    keep = set()
                    for w in words:
                        keep.update(
                            r[0] for r in conn.execute(
                                "SELECT id FROM knowledge_entries WHERE id IN (%s) AND (title LIKE ? OR body LIKE ?)" % ph,
                                tuple(ids) + ("%" + w + "%", "%" + w + "%"),
                            )
                        )
                        if not keep:
                            break
                    rows = [c for c in cand if c[0] in keep][:limit]
                relaxed = bool(rows)
        if not rows:
            # FTS5 用 unicode61 分词，中文不分词 → 长中文词常 FTS 零命中，必须靠 LIKE 兜底，
            # 否则「增值税法 实施条例」这类查询会落到无关文档上。
            # 降级顺序：① 整句字面子串（最精确）→ ② 逐词 AND → ③ 逐词 OR（最宽松）。
            like = "%" + query.strip() + "%"
            rows = conn.execute(
                """SELECT id, title, document_group, tags_json, type, substr(body,1,300)
                   FROM knowledge_entries
                   WHERE status='active' AND knowledge_base_id=? AND (title LIKE ? OR body LIKE ?)
                   ORDER BY length(title) LIMIT ?""",
                (kb_id, like, like, limit),
            ).fetchall()
            words = [w for w in query.replace('"', " ").split() if w][:8]
            if not rows and len(words) > 1:
                where = " AND ".join(["(title LIKE ? OR body LIKE ?)"] * len(words))
                args = []
                for w in words:
                    args += ["%" + w + "%", "%" + w + "%"]
                rows = conn.execute(
                    """SELECT id, title, document_group, tags_json, type, substr(body,1,300)
                       FROM knowledge_entries
                       WHERE status='active' AND knowledge_base_id=? AND """ + where + """
                       ORDER BY length(title) LIMIT ?""",
                    tuple([kb_id] + args + [limit]),
                ).fetchall()
                relaxed = bool(rows)
            if not rows and len(words) > 1:
                where = " OR ".join(["(title LIKE ? OR body LIKE ?)"] * len(words))
                args = []
                for w in words:
                    args += ["%" + w + "%", "%" + w + "%"]
                rows = conn.execute(
                    """SELECT id, title, document_group, tags_json, type, substr(body,1,300)
                       FROM knowledge_entries
                       WHERE status='active' AND knowledge_base_id=? AND """ + where + """
                       ORDER BY length(title) LIMIT ?""",
                    tuple([kb_id] + args + [limit]),
                ).fetchall()
                relaxed = bool(rows)
    finally:
        conn.close()

    if not rows:
        return "「%s」里没有命中「%s」的文档。可换同义词（如 报关单/申报单、归类/HS编码）或先用 kb_groups 看分组；若怀疑查错了库，调 kb_list 看看有哪些库。" % (
            kb_name, query)

    head = "命中 %d 篇（%s）：" % (len(rows), kb_name)
    if relaxed:
        head += "\n（原查询的所有词无法在同一篇中共现，已降级为「任一词命中」；命中项可能只覆盖部分关键词，请用 kb_read 核实）"
    if not relaxed and rows and len([w for w in query.split() if w]) > 1:
        pass  # 逐词 AND 命中即精确匹配，无需提示
    out = [head]
    for i, (kid, title, group, tags, typ, frag) in enumerate(rows, 1):
        try:
            tag_list = "、".join(json.loads(tags or "[]"))
        except Exception:
            tag_list = ""
        out.append(
            "\n[%d] %s\n    分组：%s ｜ 类型：%s ｜ 标签：%s\n    id：%s\n    片段：%s"
            % (i, title, group or "—", typ, tag_list or "—", kid, (frag or "").strip()[:400])
        )
    out.append("\n需要原文请调 kb_read(id=...)。")
    return "\n".join(out)


def kb_read(kid, offset, max_chars, kb=None):
    offset = max(0, int(offset or 0))
    max_chars = max(200, min(int(max_chars or 8000), 40000))
    kb_id = None
    if kb:
        kb_id, _ = resolve_kb(kb)          # 传了 kb 才校验归属；不传则按 id 跨库直取
    conn = connect()
    try:
        sql = ("SELECT e.title, e.body, e.document_group, e.tags_json, e.type, e.updated_at, b.name "
               "FROM knowledge_entries e LEFT JOIN knowledge_bases b ON b.id = e.knowledge_base_id "
               "WHERE e.id=? AND e.status='active'")
        params = [kid]
        if kb_id:
            sql += " AND e.knowledge_base_id=?"
            params.append(kb_id)
        row = conn.execute(sql, params).fetchone()
    finally:
        conn.close()
    if not row:
        if kb_id:
            return "没有找到 id=%s 的文档（可能已删除，或不属于指定的知识库 %s）。" % (kid, kb)
        return "没有找到 id=%s 的文档（可能已删除）。" % kid
    title, body, group, tags, typ, updated, kb_name = row
    total = len(body)
    chunk = body[offset:offset + max_chars]
    head = "# %s\n知识库：%s ｜ 分组：%s ｜ 类型：%s ｜ 更新：%s ｜ 全文 %d 字符\n" % (
        title, kb_name or "—", group, typ, updated, total)
    if offset + max_chars < total:
        head += "（当前返回 %d-%d，还有 %d 字符，继续读请传 offset=%d）\n" % (
            offset, offset + len(chunk), total - offset - len(chunk), offset + len(chunk))
    return head + "\n" + chunk


def kb_groups(kb=None):
    kb_id, kb_name = resolve_kb(kb)
    conn = connect()
    try:
        rows = conn.execute(
            "SELECT document_group, COUNT(*) FROM knowledge_entries "
            "WHERE status='active' AND knowledge_base_id=? GROUP BY document_group ORDER BY COUNT(*) DESC",
            (kb_id,),
        ).fetchall()
        total = conn.execute(
            "SELECT COUNT(*) FROM knowledge_entries WHERE status='active' AND knowledge_base_id=?", (kb_id,)
        ).fetchone()[0]
    finally:
        conn.close()
    out = ["%s共 %d 篇，按分组：" % (kb_name, total)]
    for g, n in rows:
        out.append("  - %s：%d 篇" % (g or "未分组", n))
    if not rows:
        out.append("  （空库，还没有导入资料）")
    return "\n".join(out)


def call_tool(name, args):
    if name == "kb_list":
        return kb_list()
    if name == "kb_search":
        return kb_search(args.get("query", ""), args.get("limit", 6), args.get("kb"))
    if name == "kb_read":
        return kb_read(args.get("id", ""), args.get("offset", 0), args.get("max_chars", 8000), args.get("kb"))
    if name == "kb_groups":
        return kb_groups(args.get("kb"))
    raise ValueError("unknown tool: " + name)


def handle(req):
    method = req.get("method")
    rid = req.get("id")

    if method == "initialize":
        return {"jsonrpc": "2.0", "id": rid, "result": {
            "protocolVersion": PROTOCOL,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "waimao-kb", "version": "1.0.0"},
        }}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": TOOLS}}
    if method == "tools/call":
        params = req.get("params") or {}
        name = params.get("name", "")
        args = params.get("arguments") or {}
        try:
            text = call_tool(name, args)
            return {"jsonrpc": "2.0", "id": rid, "result": {
                "content": [{"type": "text", "text": text}], "isError": False}}
        except Exception as exc:
            return {"jsonrpc": "2.0", "id": rid, "result": {
                "content": [{"type": "text", "text": "工具执行失败：%s" % exc}], "isError": True}}
    if method == "ping":
        return {"jsonrpc": "2.0", "id": rid, "result": {}}
    if method and method.startswith("notifications/"):
        return None
    if rid is None:
        return None
    return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": "method not found: " + str(method)}}


def main():
    for stream in (sys.stdin, sys.stdout):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except Exception:
            continue
        try:
            resp = handle(req)
        except Exception as exc:
            resp = {"jsonrpc": "2.0", "id": req.get("id"), "error": {"code": -32603, "message": str(exc)}}
        if resp is not None:
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
