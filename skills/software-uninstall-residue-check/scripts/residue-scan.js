#!/usr/bin/env node
'use strict';
/*
 * residue-scan.js - 已卸载软件残留扫描（文件系统 + 回收站）
 *
 * 只做两件事，注册表/服务/任务/进程请配合导出的清单单独查（见 SKILL.md 第 2 步）。
 *
 * Usage:
 *   node residue-scan.js --keys "ifind,hexin,eastmoney,同花顺" --roots "C:\,D:\,E:\" --out residue.json
 *
 * 选项：
 *   --keys    逗号分隔的关键词。ASCII 词自动加词边界，CJK 词按子串匹配。
 *   --roots   逗号分隔的扫描根，默认 "C:\"
 *   --max     并发，默认 64
 *   --top     控制台打印条数，默认 40
 *
 * 关键设计：
 *   1) 严格词边界 —— 短关键词（≤3 字符）不加边界会大量误报（em_ 命中 System_）
 *   2) 内置噪声过滤 —— WinSxS / ClickOnce / 厂商日志 / 浏览器 IndexedDB
 *   3) 回收站 $I 解析 —— 还原被删除文件的原始路径，避免用户误清自己的数据
 *   4) 所有输出写 UTF-8 文件，中文路径用 Read 工具看，不要依赖控制台
 */

const fs = require('fs');
const fsp = fs.promises;
const path = require('path');

function arg(name, def) {
  const i = process.argv.indexOf('--' + name);
  return i >= 0 && process.argv[i + 1] ? process.argv[i + 1] : def;
}

const KEYS = arg('keys', '').split(',').map(s => s.trim()).filter(Boolean);
if (!KEYS.length) { console.error('必须提供 --keys，例如 --keys "ifind,hexin,eastmoney"'); process.exit(1); }
const ROOTS = arg('roots', 'C:\\').split(',').map(s => s.trim()).filter(Boolean)
  .map(s => s.replace(/[\\/]+$/, '') + '\\');
const OUT = arg('out', path.join(process.cwd(), 'residue.json'));
const MAX = parseInt(arg('max', '64'), 10);
const TOP = parseInt(arg('top', '40'), 10);
const DEADLINE = Date.now() + 40 * 60 * 1000;

// 关键词：纯 ASCII 的加词边界；含非 ASCII 的按子串
const MATCHERS = KEYS.map(k => {
  const esc = k.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const asciiOnly = /^[\x20-\x7E]+$/.test(k);
  return { k, re: asciiOnly ? new RegExp('(^|[^a-z0-9])' + esc, 'i') : new RegExp(esc, 'i'), asciiOnly };
});

// 已知噪声源：这些路径下的命中一律丢弃
const NOISE = [
  /\\Windows\\WinSxS\\/i,
  /\\Windows\\Microsoft\.NET\\/i,
  /\\Windows\\assembly\\/i,
  /\\Windows\\servicing\\/i,
  /\\Windows\\SoftwareDistribution\\/i,
  /\\AppData\\Local\\Apps\\2\.0\\/i,
  /\\AppData\\Local\\Temp\\/i,
  /\\Windows\\Temp\\/i,
  /\\IndexedDB\\https?_/i,            // 浏览器站点数据：访问过就有，不是残留
  /ASUS System Control Interface/i,
  /\\AMD\\|\\NVIDIA Corporation\\/i,
];

function matchName(name) {
  return MATCHERS.some(m => m.re.test(name));
}
function isNoise(p) { return NOISE.some(re => re.test(p)); }

const hits = [];
let nFiles = 0, nDirs = 0, nDenied = 0, nReparse = 0;

async function walkRoot(root) {
  let active = 0;
  const q = [root];
  return new Promise(resolve => {
    async function onEnt(dir, e) {
      const full = path.join(dir, e.name);
      try {
        const st = await fsp.lstat(full);
        if (st.isSymbolicLink()) { nReparse++; return; }
        if (st.isDirectory()) {
          nDirs++;
          if (matchName(e.name) && !isNoise(full)) {
            const r = await sizeOf(full);
            hits.push({ type: 'dir', path: full, allocBytes: r.alloc, files: r.files, mtime: r.newest });
          } else {
            q.push(full);
          }
          return;
        }
        if (!st.isFile()) return;
        nFiles++;
        if (matchName(e.name) && !isNoise(full)) {
          let a = Number(st.blocks) * 512;
          if (!(a >= 0) || a > st.size + 1048576) a = 0;
          hits.push({ type: 'file', path: full, allocBytes: a, mtime: st.mtime.toISOString().slice(0, 10) });
        }
      } catch (err) { nDenied++; }
    }
    function next() {
      while (active < MAX && q.length) {
        if (Date.now() > DEADLINE) { q.length = 0; break; }
        const p = q.pop(); active++;
        fsp.readdir(p, { withFileTypes: true })
          .then(ents => Promise.all(ents.map(e => onEnt(p, e))))
          .catch(() => { nDenied++; })
          .finally(() => { active--; if (q.length === 0 && active === 0) resolve(); else next(); });
      }
      if (q.length === 0 && active === 0) resolve();
    }
    next();
  });
}

function sizeOf(root) {
  let alloc = 0, files = 0, newest = 0;
  const stack = [root];
  while (stack.length) {
    const c = stack.pop();
    let ents;
    try { ents = fs.readdirSync(c, { withFileTypes: true }); } catch (x) { continue; }
    for (const e of ents) {
      const fp = path.join(c, e.name);
      let st;
      try { st = fs.lstatSync(fp); } catch (x) { continue; }
      if (st.isSymbolicLink()) continue;
      if (st.isDirectory()) { stack.push(fp); continue; }
      files++;
      let a = Number(st.blocks) * 512;
      if (!(a >= 0) || a > st.size + 1048576) a = 0;
      alloc += a;
      if (st.mtimeMs > newest) newest = st.mtimeMs;
    }
  }
  return { alloc, files, newest: newest ? new Date(newest).toISOString().slice(0, 10) : '-' };
}

// 回收站 $I 解析：8 头 + 8 大小 + 8 时间 + UTF-16LE 原路径
function parseRecycleBin(root) {
  const out = [];
  const BIN = path.join(root, '$RECYCLE.BIN');
  let sids;
  try { sids = fs.readdirSync(BIN, { withFileTypes: true }); } catch (x) { return out; }
  for (const sid of sids) {
    if (!sid.isDirectory()) continue;
    const dir = path.join(BIN, sid.name);
    let names;
    try { names = fs.readdirSync(dir); } catch (x) { out.push({ sid: sid.name, denied: true }); continue; }
    const iMap = new Map();
    for (const f of names.filter(n => n.startsWith('$I'))) {
      try {
        const b = fs.readFileSync(path.join(dir, f));
        if (b.length < 24) continue;
        iMap.set('$R' + f.slice(2), {
          orig: b.slice(24).toString('utf16le').replace(/\0+$/, ''),
          size: Number(b.readBigUInt64LE(8)),
        });
      } catch (x) { /* 忽略损坏的 $I */ }
    }
    for (const f of names.filter(n => n.startsWith('$R'))) {
      const fp = path.join(dir, f);
      let st; try { st = fs.lstatSync(fp); } catch (x) { continue; }
      const size = st.isDirectory() ? sizeOf(fp).alloc
        : (() => { let a = Number(st.blocks) * 512; if (!(a >= 0) || a > st.size + 1048576) a = 0; return a; })();
      const info = iMap.get(f) || { orig: '(无对应 $I 记录)', size: 0 };
      out.push({ sid: sid.name, entry: f, allocBytes: size, originalPath: info.orig });
    }
  }
  return out;
}

(async () => {
  const t0 = Date.now();
  for (const r of ROOTS) {
    if (!fs.existsSync(r)) continue;
    await walkRoot(r);
  }

  const recycle = [];
  for (const r of ROOTS) recycle.push(...parseRecycleBin(r));

  hits.sort((a, b) => b.allocBytes - a.allocBytes);
  recycle.sort((a, b) => (b.allocBytes || 0) - (a.allocBytes || 0));

  const result = {
    scannedAt: new Date().toISOString(),
    elapsedSec: Math.round((Date.now() - t0) / 1000),
    roots: ROOTS,
    keys: KEYS,
    counts: { files: nFiles, dirs: nDirs, denied: nDenied, reparseSkipped: nReparse, hits: hits.length },
    hits,
    recycleBin: recycle,
  };
  fs.writeFileSync(OUT, JSON.stringify(result, null, 2), 'utf8');

  const mb = b => (b / 1048576).toFixed(1);
  console.log('DONE ' + result.elapsedSec + 's  files/dirs ' + nFiles + '/' + nDirs + '  denied ' + nDenied);
  console.log('文件系统命中 ' + hits.length + ' 项；回收站条目 ' + recycle.filter(r => !r.denied).length + ' 项');
  console.log('');
  console.log('--- 体积最大的 ' + TOP + ' 项（中文路径请用 Read 工具看 JSON）---');
  for (const h of hits.slice(0, TOP)) {
    console.log('  ' + mb(h.allocBytes).padStart(9) + ' MB  ' + h.type.padEnd(4) + ' ' + (h.mtime || '-') + '  ' + h.path);
  }
  if (hits.length > TOP) console.log('  ... 其余 ' + (hits.length - TOP) + ' 项见 JSON');
  console.log('');
  console.log('--- 回收站（清空前请逐项确认，可能夹带用户数据）---');
  for (const r of recycle.slice(0, 30)) {
    if (r.denied) { console.log('  [无权访问] ' + r.sid + '（通常为 SYSTEM，属正常）'); continue; }
    console.log('  ' + mb(r.allocBytes).padStart(9) + ' MB  ' + r.originalPath);
  }
  console.log('');
  console.log('written to ' + OUT);
})().catch(e => { console.error('FATAL', e); process.exit(1); });
