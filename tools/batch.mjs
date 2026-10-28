#!/usr/bin/env node
// batch.mjs — 一轮多件事合成一次回包（实装 AGENTS.md 第 2 节「批量执行」）
//
// 用法:
//   node batch.mjs <plan.json>        # 按计划文件执行
//   node batch.mjs --help
//
// 计划文件格式（数组，按顺序执行）:
//   [
//     {"type":"bash",    "label":"看版本",   "cmd":"grep '\"version\"' package.json | head -1"},
//     {"type":"glob",    "label":"找脚本",   "pattern":"scripts/*.mjs", "cwd":"."},
//     {"type":"grep",    "label":"找符号",   "pattern":"cacheRoot|LOCALAPPDATA", "path":"lib", "include":"*.js"},
//     {"type":"read",    "label":"读片段",   "path":"lib/index.js", "offset":36, "limit":60},
//     {"type":"exists",  "label":"核对文件", "paths":["a.txt","b/c.md"]}
//   ]
//
// 设计取舍（2026-10-29 实测依据）:
//   - 每条命令单发一轮，平均回包 1KB，却要重发 8 万 token 上下文；本脚本把 N 件事
//     合成 1 次调用、1 份回包。
//   - 输出默认截断（每项 head/tail 各 N 行），避免把整份日志塞回上下文。
//   - 任一项失败不中断其余项（除 --fail-fast），最后汇总失败清单。
import { execSync } from 'node:child_process';
import { readFileSync, existsSync, statSync, readdirSync } from 'node:fs';
import { join, isAbsolute, resolve } from 'node:path';

const args = process.argv.slice(2);
if (!args.length || args.includes('--help') || args.includes('-h')) {
  console.log(readFileSync(new URL(import.meta.url), 'utf8').split('\n').slice(1, 26).join('\n'));
  process.exit(0);
}
const planPath = args[0];
const failFast = args.includes('--fail-fast');
const headLines = Number((args.find((a) => a.startsWith('--head=')) ?? '--head=12').split('=')[1]);
const tailLines = Number((args.find((a) => a.startsWith('--tail=')) ?? '--tail=4').split('=')[1]);
const maxItemBytes = Number((args.find((a) => a.startsWith('--max=')) ?? '--max=4000').split('=')[1]);

const plan = JSON.parse(readFileSync(planPath, 'utf8'));
const clip = (s) => {
  const str = String(s ?? '');
  const lines = str.split('\n');
  let out = str;
  if (lines.length > headLines + tailLines) {
    out = [...lines.slice(0, headLines), `  …（省略 ${lines.length - headLines - tailLines} 行）…`, ...lines.slice(-tailLines)].join('\n');
  }
  if (out.length > maxItemBytes) out = out.slice(0, maxItemBytes) + `\n  …（截断，原文 ${out.length} 字节）`;
  return out;
};

const results = [];
const failures = [];
const t0 = Date.now();

for (const item of plan) {
  const label = item.label ?? item.type;
  const started = Date.now();
  let body = '';
  try {
    if (item.type === 'bash') {
      body = execSync(item.cmd, { shell: 'bash', cwd: item.cwd, encoding: 'utf8', timeout: item.timeout ?? 120000, stdio: ['ignore', 'pipe', 'pipe'] });
      if (!body.trim()) body = '(无输出)';
    } else if (item.type === 'exists') {
      body = (item.paths ?? []).map((p) => {
        if (!existsSync(p)) return `MISS ${p}`;
        const st = statSync(p);
        return `OK   ${p}  ${st.isDirectory() ? 'dir' : `${st.size}B`}`;
      }).join('\n');
    } else if (item.type === 'glob') {
      const root = resolve(item.cwd ?? '.');
      const rx = new RegExp('^' + String(item.pattern).replace(/[.+^${}()|[\]\\]/g, '\\$&').replace(/\*\*/g, '\u0000').replace(/\*/g, '[^/]*').replace(/\u0000/g, '.*') + '$');
      const hits = [];
      const walk = (dir, rel) => {
        let entries = [];
        try { entries = readdirSync(dir, { withFileTypes: true }); } catch { return; }
        for (const e of entries) {
          const r = rel ? `${rel}/${e.name}` : e.name;
          if (e.isDirectory()) { if (!/node_modules|\.git/.test(e.name)) walk(join(dir, e.name), r); }
          else if (rx.test(r)) hits.push(r);
        }
      };
      walk(root, '');
      body = hits.length ? hits.slice(0, 200).join('\n') : '(无匹配)';
    } else if (item.type === 'grep') {
      const inc = item.include ? `--include='${item.include}'` : '';
      const cmd = `grep -rn ${inc} -E ${JSON.stringify(item.pattern)} ${JSON.stringify(item.path ?? '.')} 2>/dev/null | head -${item.head ?? 40}`;
      try { body = execSync(cmd, { shell: 'bash', encoding: 'utf8', timeout: 60000 }); } catch (e) { body = e.stdout || '(无匹配)'; }
    } else if (item.type === 'read') {
      const lines = readFileSync(item.path, 'utf8').split('\n');
      const off = Math.max(0, (item.offset ?? 1) - 1);
      const lim = item.limit ?? 60;
      body = lines.slice(off, off + lim).map((l, i) => `${String(off + i + 1).padStart(5)}  ${l}`).join('\n');
      body += `\n(文件共 ${lines.length} 行)`;
    } else {
      body = `未知类型: ${item.type}`;
    }
  } catch (error) {
    body = `[失败] ${String(error.stderr ?? '').trim() || error.message}`;
    failures.push(label);
    if (failFast) { results.push({ label, body, ok: false, ms: Date.now() - started }); break; }
  }
  results.push({ label, body, ok: !failures.includes(label), ms: Date.now() - started });
}

// ---- 一次性输出 ----
const out = [];
out.push(`# batch: ${results.length} 项，失败 ${failures.length} 项，耗时 ${Date.now() - t0} ms`);
for (const r of results) {
  out.push(`\n## ${r.ok ? '✓' : '✗'} ${r.label}  (${r.ms}ms)`);
  out.push(clip(r.body));
}
if (failures.length) out.push(`\n# 失败清单: ${failures.join(', ')}`);
console.log(out.join('\n'));
process.exit(failures.length && failFast ? 1 : 0);
