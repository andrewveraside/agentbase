# -*- coding: utf-8 -*-
"""
按工作表把一个 xlsx 拆成多个「单 sheet」工作簿。

用法:
  python split_by_sheet.py <源文件.xlsx> [输出目录] [--exclude 表1 表2 ...] [--include-hidden] [--prefix 前缀]

特点:
  - ZIP/XML 层级切分：目标工作表的 sheetN.xml 字节原样搬运，
    不经过 openpyxl 重写，条件格式 / 样式 / 列宽 / 合并单元格 / 自动筛选 100% 保留。
  - 只重写 workbook.xml、workbook.xml.rels、[Content_Types].xml、docProps/app.xml。
  - 速度取决于体积而非数据量解析，几十 MB 的文件也很快。

依赖: 仅标准库。
"""
import os
import re
import io
import sys
import argparse
import zipfile
from xml.etree import ElementTree as ET

NS_MAIN  = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_REL   = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_PKG   = "http://schemas.openxmlformats.org/package/2006/relationships"
NS_CT    = "http://schemas.openxmlformats.org/package/2006/content-types"
NS_EP    = "http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
NS_X15   = "http://schemas.microsoft.com/office/spreadsheetml/2010/11/main"
NS_X15AC = "http://schemas.microsoft.com/office/spreadsheetml/2010/11/ac"
NS_MC    = "http://schemas.openxmlformats.org/markup-compatibility/2006"
NS_DBS   = "http://web.wps.cn/et/2021/dbsheet"

for _p, _u in [("", NS_MAIN), ("r", NS_REL), ("mc", NS_MC), ("x15", NS_X15),
               ("x15ac", NS_X15AC), ("dbsheet", NS_DBS), ("", NS_CT), ("", NS_PKG)]:
    try:
        ET.register_namespace(_p, _u)
    except ValueError:
        pass


def q(ns, tag):
    return f"{{{ns}}}{tag}"


INVALID = re.compile(r'[\\/:*?"<>|]')


def safe_name(s):
    s = INVALID.sub("_", s).strip().strip(".")
    return s or "sheet"


def fresh_zip(raw: bytes) -> zipfile.ZipFile:
    """源文件整份读进内存，避免多句柄 seek 冲突（Python zipfile 边读边开的坑）"""
    return zipfile.ZipFile(io.BytesIO(raw))


def write_single(src_zip, part_to_keep, wb_root, rels_root, ct_root, app_root, out_path):
    for tag in ("HeadingPairs", "TitlesOfParts"):
        if app_root is not None:
            el = app_root.find(q(NS_EP, tag))
            if el is not None:
                app_root.remove(el)

    new_wb   = ET.tostring(wb_root, encoding="UTF-8", xml_declaration=True)
    new_rels = ET.tostring(rels_root, encoding="UTF-8", xml_declaration=True)
    new_ct   = ET.tostring(ct_root, encoding="UTF-8", xml_declaration=True)
    new_app  = ET.tostring(app_root, encoding="UTF-8", xml_declaration=True) if app_root is not None else None

    target_in_zip = part_to_keep.lstrip("/")
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zo:
        for item in src_zip.infolist():
            n = item.filename
            if item.is_dir():
                zo.writestr(item, b"")
                continue
            if n == "xl/workbook.xml":
                zo.writestr(item, new_wb)
            elif n == "xl/_rels/workbook.xml.rels":
                zo.writestr(item, new_rels)
            elif n == "[Content_Types].xml":
                zo.writestr(item, new_ct)
            elif n == "docProps/app.xml" and new_app is not None:
                zo.writestr(item, new_app)
            elif n.startswith("xl/worksheets/") and n != target_in_zip:
                continue
            else:
                zo.writestr(item, src_zip.read(n))


def split(src, outdir, exclude=(), include_hidden=False, prefix=""):
    os.makedirs(outdir, exist_ok=True)
    with open(src, "rb") as f:
        raw = f.read()

    z0 = fresh_zip(raw)
    wb0 = ET.fromstring(z0.read("xl/workbook.xml"))
    rels0 = ET.fromstring(z0.read("xl/_rels/workbook.xml.rels"))
    try:
        app0 = ET.fromstring(z0.read("docProps/app.xml"))
    except KeyError:
        app0 = None
    rid_map = {r.get("Id"): r.get("Target") for r in rels0}
    entries = [(i, s.get("name"), s.get(q(NS_REL, "id")), s.get("state"))
               for i, s in enumerate(wb0.find(q(NS_MAIN, "sheets")))]
    z0.close()

    log, made = [], []
    for idx, name, rid, state in entries:
        if name in exclude:
            log.append(f"[skip] {name}  排除名单")
            continue
        zz = fresh_zip(raw)
        part = "/xl/" + rid_map[rid].lstrip("/")
        xml = zz.read(part.lstrip("/"))
        if state == "hidden" and not include_hidden and b"<row" not in xml:
            log.append(f"[skip] {name}  隐藏空表已忽略（--include-hidden 可强制导出）")
            zz.close()
            continue

        wb2 = ET.fromstring(zz.read("xl/workbook.xml"))
        rl2 = ET.fromstring(zz.read("xl/_rels/workbook.xml.rels"))
        ct2 = ET.fromstring(zz.read("[Content_Types].xml"))
        ap2 = ET.fromstring(zz.read("docProps/app.xml")) if app0 is not None else None

        # workbook.xml: 只留目标表
        sheets_el = wb2.find(q(NS_MAIN, "sheets"))
        hit = None
        for s in list(sheets_el):
            if s.get(q(NS_REL, "id")) == rid:
                hit = s
            else:
                sheets_el.remove(s)
        hit.set("sheetId", "1")
        hit.set(q(NS_REL, "id"), "rId1")

        # definedNames: 留全局的 + 本表的（本地序号归 0）
        dn = wb2.find(q(NS_MAIN, "definedNames"))
        if dn is not None:
            keep = []
            for d in dn:
                lsi = d.get("localSheetId")
                if lsi is None:
                    keep.append(d)
                elif int(lsi) == idx:
                    d.set("localSheetId", "0")
                    keep.append(d)
            for d in list(dn):
                dn.remove(d)
            dn.extend(keep)
            if len(dn) == 0:
                wb2.remove(dn)

        # rels: 留 theme/styles/sharedStrings + 目标表（重编号 rId1）
        parts = set()
        for rel in list(rl2):
            t = rel.get("Type", "")
            if t.endswith("/worksheet") or "/worksheets/" in rel.get("Target", ""):
                if rel.get("Id") == rid:
                    rel.set("Id", "rId1")
                    parts.add("/xl/" + rel.get("Target").lstrip("/"))
                else:
                    rl2.remove(rel)
            elif t.endswith(("/theme", "/styles", "/sharedStrings")):
                parts.add("/xl/" + rel.get("Target").lstrip("/"))

        for o in list(ct2):
            pn = o.get("PartName", "")
            if pn.startswith("/xl/worksheets/") and pn not in parts:
                ct2.remove(o)

        fn = prefix + safe_name(name) + ".xlsx"
        out_path = os.path.join(outdir, fn)
        write_single(zz, part, wb2, rl2, ct2, ap2, out_path)
        zz.close()
        made.append((fn, name, os.path.getsize(out_path)))

    total = sum(m[2] for m in made)
    log.append(f"完成：{len(made)} 个文件，合计 {total/1024/1024:,.1f} MB -> {outdir}")
    return made, log


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("outdir", nargs="?", default="")
    ap.add_argument("--exclude", nargs="*", default=[])
    ap.add_argument("--include-hidden", action="store_true")
    ap.add_argument("--prefix", default="")
    a = ap.parse_args()

    outdir = a.outdir or os.path.join(os.path.dirname(os.path.abspath(a.src)), "拆分结果")
    made, log = split(a.src, outdir, set(a.exclude), a.include_hidden, a.prefix)
    print("\n".join(log))
    for fn, name, size in made:
        print(f"  {fn}\t{size/1024:,.0f} KB")


if __name__ == "__main__":
    main()
