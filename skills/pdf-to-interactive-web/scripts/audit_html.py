#!/usr/bin/env python3
"""Self-check a generated single-file interactive page (stdlib only).

usage: python3 audit_html.py index.html [--budget 2500] [--list 40]

Reports: external resources, default-visible CJK characters (outside <details>),
the data-* markers from references/page-contract.md, reader features, citations
pointing at unknown SOURCES ids, and text blocks that contain numbers but no citation.
"""
import argparse
import re
import sys
from html.parser import HTMLParser

CJK = re.compile(r"[㐀-鿿]")
NUM = re.compile(r"\d|[一二三四五六七八九十百千万亿]+\s*(?:倍|%|成|亿|万|个|岁|年|页|字|屏|处)")
SKIP = {"script", "style", "template", "noscript", "svg"}
BLOCK = {"p", "li", "h1", "h2", "h3", "h4", "h5", "h6", "td", "th", "figcaption", "blockquote", "dd", "dt", "caption"}
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []          # (tag, hidden_or_folded)
        self.visible = []
        self.blocks = []         # [text, has_cite]
        self.block_depth = []
        self.markers = {}
        self.cite_ids = []
        self.external = []
        self.has_viewport = False

    def _hidden(self):
        return any(h for _, h in self.stack)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        for k in a:
            if k.startswith("data-"):
                self.markers[k] = self.markers.get(k, 0) + 1
        if a.get("data-cite"):
            self.cite_ids.append(a["data-cite"])
            if self.block_depth:
                self.blocks[self.block_depth[-1]][1] = True
        if tag == "meta" and a.get("name") == "viewport":
            self.has_viewport = True
        for attr in ("src", "href"):
            v = a.get(attr) or ""
            if re.match(r"(https?:)?//", v) and not (tag == "a" and attr == "href"):
                self.external.append(f"<{tag} {attr}={v[:90]}>")
        if tag in VOID:
            return
        hidden = "hidden" in a or a.get("aria-hidden") == "true"
        self.stack.append((tag, hidden))
        if tag in BLOCK:
            self.blocks.append(["", False])
            self.block_depth.append(len(self.blocks) - 1)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        while self.stack:
            t, _ = self.stack.pop()
            if t in BLOCK and self.block_depth:
                self.block_depth.pop()
            if t == tag:
                break

    def handle_data(self, data):
        tags = [t for t, _ in self.stack]
        if any(t in SKIP for t in tags):
            return
        hidden = any(h for _, h in self.stack)
        folded = "details" in tags and "summary" not in tags
        if not hidden and not folded:
            self.visible.append(data)
        if self.block_depth:
            self.blocks[self.block_depth[-1]][0] += data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("html")
    ap.add_argument("--budget", type=int, default=2500)
    ap.add_argument("--list", type=int, default=40)
    a = ap.parse_args()
    src = open(a.html, encoding="utf-8", errors="replace").read()
    p = Page()
    p.feed(src)

    scripts = "\n".join(re.findall(r"<script[^>]*>(.*?)</script>", src, re.S | re.I))
    styles = "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", src, re.S | re.I))
    ext = list(p.external)
    ext += [f"css url({u[:90]})" for u in re.findall(r"url\(\s*['\"]?((?:https?:)?//[^'\")]+)", styles)]
    ext += [f"@import {u[:90]}" for u in re.findall(r"@import\s+(?:url\()?['\"]?((?:https?:)?//[^'\")\s;]+)", styles)]

    visible_cjk = len(CJK.findall("".join(p.visible)))
    script_cjk = len(CJK.findall(scripts))
    source_ids = set(re.findall(r"['\"]?([\w-]+)['\"]?\s*:\s*\{\s*page\s*:", scripts))
    unknown = sorted({c for c in p.cite_ids if source_ids and c not in source_ids})
    scenes = len(set(re.findall(r'data-scene="([^"]*)"', src)))

    feats = {
        "记住阅读进度 localStorage": "localStorage" in src,
        "减弱动画 prefers-reduced-motion": "prefers-reduced-motion" in src,
        "明暗 prefers-color-scheme": "prefers-color-scheme" in src,
        "返回键 pushState/popstate": bool(re.search(r"pushState|popstate", src)),
        "手机 viewport": p.has_viewport,
    }
    problems = []
    if ext:
        problems.append(f"有 {len(ext)} 个外部资源（国内可能加载失败，离线不可用）")
    if visible_cjk > a.budget:
        problems.append(f"默认可见汉字 {visible_cjk} 超过上限 {a.budget}")
    if scenes > 7:
        problems.append(f"场景 {scenes} 个，超过 7 个")
    if p.markers.get("data-guess", 0) < 2:
        problems.append("「先猜再看」少于 2 处（data-guess）")
    if not p.markers.get("data-quiz"):
        problems.append("没有结尾自测（data-quiz）")
    figs = p.markers.get("data-figure", 0)
    if figs and not 2 <= figs <= 4:
        problems.append(f"主视觉 {figs} 幅，建议 2–4 幅")
    if unknown:
        problems.append(f"{len(unknown)} 个角标指向 SOURCES 里不存在的 id：{', '.join(unknown[:10])}")
    problems += [f"缺少：{k}" for k, v in feats.items() if not v]

    print(f"# 自检报告：{a.html}\n")
    print(f"- 文件大小：{len(src.encode('utf-8')) / 1024:.0f} KB")
    print(f"- 默认可见汉字：{visible_cjk}（上限 {a.budget}；不含 <details> 折叠内容）")
    print(f"- 脚本里的汉字：{script_cjk}" + ("（较多：如果正文由 JS 生成，上面的可见字数会偏低，正文应写进 HTML）" if script_cjk > 800 else ""))
    print(f"- 场景：{scenes}；首屏 data-hero：{p.markers.get('data-hero', 0)}；主视觉：{figs}")
    print(f"- 出处角标：{len(p.cite_ids)}（SOURCES 里 {len(source_ids)} 条）")
    print(f"- 先猜再看：{p.markers.get('data-guess', 0)}；自测：{p.markers.get('data-quiz', 0)}")
    labels = re.findall(r'data-label="([^"]+)"', src)
    if labels:
        print("- 内容标签：" + "、".join(f"{k} {labels.count(k)}" for k in sorted(set(labels))))
    for k, v in feats.items():
        print(f"- {k}：{'有' if v else '无'}")
    if ext:
        print("\n## 外部资源")
        for e in ext[:20]:
            print(f"- {e}")

    uncited = [re.sub(r"\s+", " ", t).strip() for t, c in p.blocks if not c and NUM.search(t)]
    uncited = [t for t in uncited if len(t) > 4]
    print(f"\n## 含数字但没有角标的段落（{len(uncited)}）")
    print("逐条确认：要么补角标，要么标成推算 / 示意，要么删掉。")
    for t in uncited[: a.list]:
        print(f"- {t[:120]}")

    print("\n## 结论")
    if problems:
        for x in problems:
            print(f"- [ ] {x}")
    else:
        print("- 结构检查全部通过。仍需人工核对：页面上最「硬」的 12 处说法（见 references/fidelity-checklist.md）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
