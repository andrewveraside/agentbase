#!/usr/bin/env node
'use strict';
/*
 * profile.js - 多维占用画像（一次遍历，四张表）
 *
 * 与 cscan.js 的分工：
 *   cscan.js   -> 只做目录聚合，回答"哪个目录大"
 *   profile.js -> 目录聚合 + 扩展名聚合 + 体积分档 + 最大文件，回答"是什么占的"
 *
 * 当用户说"把文件按大小分类""看看都是些什么文件"时用这个。
 *
 * Usage:
 *   node profile.js [--root D:\] [--out scan-profile.json]
 *                   [--max 64] [--min-big-mb 200] [--top-ext 40] [--level 2]
 *
 * 注意：--root 传子目录也能跑，但 reconciliation 差额会失去意义（分母是整卷已用）。
 *       要校验账目闭合，--root 必须是卷根。
 *
 * 沿用 cscan.js 的核心方法：blocks*512 算实占、跳过重解析点、钳制异常 blocks。
 */

const fs = require('fs');
const fsp = fs.promises;
const path = require('path');

function arg(name, def) {
  const i = process.argv.indexOf('--' + name);
  return i >= 0 && process.argv[i + 1] ? process.argv[i + 1] : def;
}
const ROOT = arg('root', 'C:\\').replace(/[\\/]+$/, '') + '\\';
const OUT = arg('out', path.join(process.cwd(), 'scan-profile.json'));
const MAX = parseInt(arg('max', '64'), 10);
const MIN_BIG = parseFloat(arg('min-big-mb', '200')) * 1048576;
const TOP_EXT = parseInt(arg('top-ext', '40'), 10);
const LEVEL = parseInt(arg('level', '2'), 10);
const DEADLINE = Date.now() + 40 * 60 * 1000;

const gb = b => +(b / 1073741824).toFixed(3);

const dirAgg = new Map();
const extAgg = new Map();
const buckets = new Map([
  ['<1MB', { alloc: 0, files: 0 }],
  ['1-10MB', { alloc: 0, files: 0 }],
  ['10-100MB', { alloc: 0, files: 0 }],
  ['100MB-1GB', { alloc: 0, files: 0 }],
  ['>1GB', { alloc: 0, files: 0 }],
]);
const bigFiles = [];
let nFiles = 0, nDirs = 0, sumAlloc = 0, sumLogical = 0, nReparse = 0, nDenied = 0, nClamped = 0;

function bucketOf(a) {
  if (a < 1048576) return '<1MB';
  if (a < 10 * 1048576) return '1-10MB';
  if (a < 100 * 1048576) return '10-100MB';
  if (a < 1073741824) return '100MB-1GB';
  return '>1GB';
}

// 注意：游戏资源里有 3C / 0G / 3A 这类没有扩展名的切片文件，会全部落进 (无扩展名) 桶里，
// 表现为"体积巨大但看不出是什么"。遇到这种先查 topFiles 里同目录的文件再判断。
function extOf(name) {
  const i = name.lastIndexOf('.');
  if (i <= 0 || i === name.length - 1) return '(无扩展名)';
  const e = name.slice(i + 1).toLowerCase();
  return e.length > 12 ? '(其他)' : '.' + e;
}

async function walk() {
  let active = 0;
  const q = [ROOT];
  return new Promise(resolve => {
    async function onEnt(dir, e) {
      const full = path.join(dir, e.name);
      try {
        const st = await fsp.lstat(full);
        if (st.isSymbolicLink()) { nReparse++; return; }
        if (st.isDirectory()) { nDirs++; q.push(full); return; }
        if (!st.isFile()) return;

        nFiles++;
        const logical = st.size;
        let alloc = Number(st.blocks) * 512;
        if (!(alloc >= 0) || alloc > logical + 1048576) { alloc = 0; nClamped++; }
        sumAlloc += alloc; sumLogical += logical;

        const parts = full.slice(ROOT.length).split(path.sep);
        for (let d = 1; d <= Math.min(LEVEL, parts.length); d++) {
          const k = parts.slice(0, d).join('\\');
          let o = dirAgg.get(k);
          if (!o) { o = { alloc: 0, logical: 0, files: 0 }; dirAgg.set(k, o); }
          o.alloc += alloc; o.logical += logical; o.files++;
        }

        const ek = extOf(e.name);
        let eo = extAgg.get(ek);
        if (!eo) { eo = { alloc: 0, logical: 0, files: 0 }; extAgg.set(ek, eo); }
        eo.alloc += alloc; eo.logical += logical; eo.files++;

        const b = buckets.get(bucketOf(alloc));
        b.alloc += alloc; b.files++;

        if (alloc >= MIN_BIG) {
          bigFiles.push({ path: full, allocGB: gb(alloc), logicalGB: gb(logical), mtime: st.mtime.toISOString().slice(0, 10) });
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
          .finally(() => {
            active--;
            if (q.length === 0 && active === 0) resolve(); else next();
          });
      }
      if (q.length === 0 && active === 0) resolve();
    }
    next();
  });
}

(async () => {
  const t0 = Date.now();
  await walk();

  const isVolumeRoot = /^[A-Za-z]:\\?$/.test(ROOT);
  if (!isVolumeRoot) {
    console.log('WARN --root 不是卷根（' + ROOT + '），reconciliation 的差额会失去意义（对比的是整卷已用）。');
    console.log('     目录/类型/分档三张表仍然有效，差额请忽略。');
  }

  const s = fs.statfsSync(ROOT);
  const volTotal = s.bsize * s.blocks;
  const volFree = s.bsize * s.bavail;
  const volUsed = volTotal - volFree;

  const dirs = [];
  for (let d = 1; d <= LEVEL; d++) {
    dirs.push(...[...dirAgg.entries()].filter(([k]) => k.split('\\').length === d)
      .map(([key, v]) => ({ level: d, key, allocGB: gb(v.alloc), logicalGB: gb(v.logical), files: v.files })));
  }

  const result = {
    scannedAt: new Date().toISOString(),
    elapsedSec: Math.round((Date.now() - t0) / 1000),
    root: ROOT,
    volume: { totalGB: gb(volTotal), usedGB: gb(volUsed), freeGB: gb(volFree) },
    totals: {
      files: nFiles, dirs: nDirs, allocatedGB: gb(sumAlloc), logicalGB: gb(sumLogical),
      reparseSkipped: nReparse, denied: nDenied, clampedBadBlocks: nClamped,
    },
    reconciliation: {
      volumeUsedGB: gb(volUsed), walkedAllocatedGB: gb(sumAlloc),
      unexplainedGB: gb(volUsed - sumAlloc),
      pctOfUsed: +(100 * (volUsed - sumAlloc) / volUsed).toFixed(1),
      note: '差额 ~= MFT + $LogFile + 卷影副本 + 无权限目录。占已用 5-8% 属正常；超过 15% 说明有整块区域没扫到。',
    },
    dirs,
    byExtension: [...extAgg.entries()].map(([ext, v]) => ({ ext, allocGB: gb(v.alloc), files: v.files }))
      .sort((a, b) => b.allocGB - a.allocGB).slice(0, TOP_EXT),
    bySizeBucket: [...buckets.entries()].map(([b, v]) => ({ bucket: b, allocGB: gb(v.alloc), files: v.files })),
    topFiles: bigFiles.sort((a, b) => b.allocGB - a.allocGB).slice(0, 60),
  };

  fs.writeFileSync(OUT, JSON.stringify(result, null, 2), 'utf8');
  console.log('DONE ' + result.elapsedSec + 's  files/dirs ' + nFiles + '/' + nDirs);
  console.log('  volumeUsed  : ' + result.volume.usedGB + ' GB');
  console.log('  walkedAlloc : ' + result.totals.allocatedGB + ' GB');
  console.log('  unexplained : ' + result.reconciliation.unexplainedGB + ' GB (' + result.reconciliation.pctOfUsed + '%)');
  console.log('  reparse/denied/clamped: ' + nReparse + '/' + nDenied + '/' + nClamped);
  console.log('  written to  : ' + OUT);
})().catch(e => { console.error('FATAL', e); process.exit(1); });
