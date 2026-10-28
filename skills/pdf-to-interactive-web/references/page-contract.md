# 页面规范

## 硬性要求

- **单文件**：HTML、CSS、JS 全在一个 `index.html` 里，双击就能打开，离线可用。
- **零外部依赖**：不引 JS 库，不引外部字体（原因见 `style-presets.md`），不引外链图片。插画用内联 SVG 或 Canvas 画。
- **约定的标记**：下面这些 `data-*` 标记让 `scripts/audit_html.py` 能自动数出场景、角标、先猜再看和自测题。用上它们，自检才有意义。

| 部件 | 标记 |
|---|---|
| 首屏 30 秒版 | `<section data-hero>` |
| 场景（最多 7 个） | `<section data-scene="1">` … |
| 出处角标 | `<sup class="cite" data-cite="来源id">` |
| 内容标签 | `<span class="tag" data-label="推算">`（可选值：推算、示意、读图、解读） |
| 先猜再看 | `<div data-guess>` |
| 结尾自测 | `<div data-quiz>` |
| 主视觉插画 | `<figure data-figure>`（2–4 个） |
| 折叠层 | `<details>` |

## 出处与回到原处

所有原句集中写在一个 `SOURCES` 对象里，这就是「事实账本」的落地形式：

```js
const SOURCES = {
  unitCases: { page: 5, quote: "The Coca-Cola system sold 33.8 billion and 33.7 billion unit cases…", zh: "2025、2024 年系统分别卖出 338 亿、337 亿单位箱" },
  // id: { page: 原文页码, quote: 原文原句（保留原语言）, zh: 中文转述 }
};
```

点角标时，弹出卡片显示原句、页码和转述，关闭后回到原来的阅读位置。从全局图、索引或角标跳到别的场景之前，先记下当前位置，并提供「回到刚才的位置」按钮，浏览器的返回键也要能用：

```js
const backStack = [];
function jumpTo(id) {
  backStack.push(scrollY);
  history.pushState({ y: scrollY }, "");
  document.getElementById(id).scrollIntoView({ behavior: motionOK() ? "smooth" : "auto" });
  backBtn.hidden = false;
}
function goBack() {
  const y = backStack.pop();
  if (y != null) scrollTo({ top: y, behavior: motionOK() ? "smooth" : "auto" });
  backBtn.hidden = backStack.length === 0;
}
addEventListener("popstate", e => { if (e.state && e.state.y != null) { backStack.pop(); scrollTo(0, e.state.y); } });
```

## 先猜再看

```html
<div data-guess>
  <p>卖浓缩液占 85% 的箱量，你猜它占收入的百分之几？</p>
  <input type="range" min="0" max="100" value="50"> <output>50%</output>
  <button>揭晓</button>
  <p class="reveal" hidden>原文：约 59%<sup class="cite" data-cite="revShare"></sup></p>
</div>
```

答案揭晓之前，不要在页面别处先把答案说出来。

## 读者设置

- 阅读进度：用 `localStorage` 记住滚动位置或当前场景，下次打开时提示「接着读」。读写都包在 `try/catch` 里，隐私模式下不能报错。
- 字号：A− / A+ 两档以上，存进 `localStorage`。
- 明暗：跟随系统（`prefers-color-scheme`），也提供手动切换。
- 动画：`prefers-reduced-motion: reduce` 时关掉滚动动画和自动播放。

```js
const motionOK = () => !matchMedia("(prefers-reduced-motion: reduce)").matches;
const store = { get(k) { try { return localStorage.getItem(k); } catch { return null; } },
                set(k, v) { try { localStorage.setItem(k, v); } catch {} } };
```

## 布局

- 手机竖屏（390px 宽）优先：没有横向滚动，触控目标至少 44px，正文至少 16px。
- 键盘：← → 切换场景，Esc 关闭弹窗。
- 默认可见文字（不含 `<details>` 里的折叠内容）全篇不超过 2500 个汉字。
- 文字要是真文字，不要画进图片里，读者要能选中、搜索和朗读。
- 正文写在 HTML 里，JS 只负责交互和动画。正文全靠 JS 生成时，自检脚本数不到字数，读屏软件和搜索也读不到。

## 交付前

运行 `python3 scripts/audit_html.py index.html`，把报告里的问题修掉。
