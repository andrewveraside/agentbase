#!/usr/bin/env node
'use strict';
/*
 * cscan.js - Windows true-usage disk audit (allocated bytes, not logical size)
 *
 * Usage:
 *   node cscan.js [--root C:\] [--out scan-result.json] [--depth 4]
 *                 [--max 64] [--min-big-mb 300] [--skip "path1,path2"]
 *
 * Key behaviours
 *   - counts st.blocks * 512 (real allocation) instead of st.size
 *   - skips reparse points (junction + symlink) so nothing is double counted
 *   - clamps garbage st.blocks values returned for some marker files
 *   - closes the loop against volume usage so you can prove nothing was missed
 */

const fs = require('fs');
const fsp = fs.promises;
const path = require('path');

function arg(name, def) {
  const i = process.argv.indexOf('--' + name);
  return i >= 0 && process.argv[i + 1] ? process.argv[i + 1] : def;
}
const ROOT = (arg('root', 'C:\\').replace(/[\\/]+$/, '')) + '\\';
const OUT = arg('out', path.join(process.cwd(), 'scan-result.json'));
const MAXDEPTH = parseInt(arg('depth', '4'), 10);
const MAX = parseInt(arg('max', '64'), 10);
const MIN_BIG_MB = parseFloat(arg('min-big-mb', '300'));
const SKIP = arg('skip', '').split(',').map(s => s.trim()).filter(Boolean).map(s => s.toLowerCase());
const DEADLINE = Date.now() + 40 * 60 * 1000; // hard stop, 40 min

const gb = b => +(b / 1073741824).toFixed(3);

const agg = new Map();
const bigFiles = [];
let nFiles = 0, nDirs = 0, sumAlloc = 0, sumLogical = 0, nReparse = 0, nDenied = 0, nClamped = 0;

function bump(key, a, l) {
  let o = agg.get(key);
  if (!o) { o = { alloc: 0, logical: 0, files: 0 }; agg.set(key, o); }
  o.alloc += a; o.logical += l; o.files++;
}

function isSkipped(p) {
  if (!SKIP.length) return false;
  const low = p.toLowerCase();
  return SKIP.some(s => low.startsWith(s));
}

async function walk() {
  let active = 0;
  const q = [ROOT];
  return new Promise(resolve => {
    async function onEnt(dir, e) {
      const full = path.join(dir, e.name);
      if (isSkipped(full)) return;
      try {
        const st = await fsp.lstat(full);
        if (st.isSymbolicLink()) { nReparse++; return; }   // junction + symlink
        if (st.isDirectory()) { nDirs++; q.push(full); return; }
        if (!st.isFile()) return;

        nFiles++;
        const logical = st.size;
        let alloc = Number(st.blocks) * 512;
        if (!(alloc >= 0) || alloc > logical + 1048576) { alloc = 0; nClamped++; }
        sumAlloc += alloc; sumLogical += logical;

        const rel = full.slice(ROOT.length);
        const parts = rel.split(path.sep);
        for (let d = 1; d <= Math.min(MAXDEPTH, parts.length); d++) {
          bump(parts.slice(0, d).join('\\'), alloc, logical);
        }
        if (alloc >= MIN_BIG_MB * 1024 * 1024) {
          bigFiles.push({
            path: full,
            allocGB: gb(alloc),
            logicalGB: gb(logical),
            mtime: st.mtime.toISOString().slice(0, 10),
          });
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

  const fsStat = fs.statfsSync(ROOT);
  const volTotal = fsStat.bsize * fsStat.blocks;
  const volFree = fsStat.bsize * fsStat.bavail;
  const volUsed = volTotal - volFree;
  const unexplained = volUsed - sumAlloc;

  const rows = [...agg.entries()].map(([k, v]) => ({
    key: k,
    depth: k.split('\\').length,
    allocGB: gb(v.alloc),
    logicalGB: gb(v.logical),
    files: v.files,
    inflate: v.alloc > 0 ? +(v.logical / v.alloc).toFixed(2) : null,
  }));
  const byDepth = d => rows.filter(r => r.depth === d).sort((a, b) => b.allocGB - a.allocGB);

  const result = {
    scannedAt: new Date().toISOString(),
    elapsedSec: Math.round((Date.now() - t0) / 1000),
    root: ROOT,
    volume: { totalGB: gb(volTotal), usedGB: gb(volUsed), freeGB: gb(volFree) },
    totals: {
      files: nFiles, dirs: nDirs,
      allocatedGB: gb(sumAlloc), logicalGB: gb(sumLogical),
      reparseSkipped: nReparse, denied: nDenied, clampedBadBlocks: nClamped,
    },
    reconciliation: {
      volumeUsedGB: gb(volUsed),
      walkedAllocatedGB: gb(sumAlloc),
      unexplainedGB: gb(unexplained),
      note: 'unexplained ~= MFT + $LogFile + shadow copies + denied dirs. 5-8% of used is normal.',
    },
    level1: byDepth(1),
    level2: byDepth(2).slice(0, 70),
    level3: byDepth(3).slice(0, 80),
    level4: byDepth(4).slice(0, 90),
    topAllocatedFiles: bigFiles.sort((a, b) => b.allocGB - a.allocGB).slice(0, 50),
  };

  fs.writeFileSync(OUT, JSON.stringify(result, null, 2), 'utf8');
  console.log('DONE ' + result.elapsedSec + 's');
  console.log('  volumeUsed     : ' + result.volume.usedGB + ' GB');
  console.log('  walkedAlloc    : ' + result.totals.allocatedGB + ' GB');
  console.log('  logical(inflated): ' + result.totals.logicalGB + ' GB');
  console.log('  unexplained    : ' + result.reconciliation.unexplainedGB + ' GB');
  console.log('  files/dirs     : ' + nFiles + ' / ' + nDirs);
  console.log('  reparse skipped: ' + nReparse + '   clamped: ' + nClamped + '   denied: ' + nDenied);
  console.log('  written to     : ' + OUT);
})().catch(e => { console.error('FATAL', e); process.exit(1); });
