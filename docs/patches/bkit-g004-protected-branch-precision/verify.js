#!/usr/bin/env node
// Verify the local G-004 precision patch on the newest installed bkit.
// Exit 0: every case behaves as the patch intends. Exit 1: re-apply (README.md).
// Trigger strings are assembled at runtime so this file's own text does not
// match the hook it is testing when it is passed through a shell.
'use strict';
const fs = require('fs');
const path = require('path');

const CACHE = path.join(process.env.HOME, '.claude/plugins/cache/bkit-marketplace/bkit');
const versions = fs.readdirSync(CACHE)
  .filter((v) => fs.existsSync(path.join(CACHE, v, 'lib/control/destructive-detector.js')))
  .sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));
if (versions.length === 0) { console.log('no bkit install found'); process.exit(1); }
const version = process.argv[2] || versions[versions.length - 1];
const detector = require(path.join(CACHE, version, 'lib/control/destructive-detector.js'));
const detect = detector.detect;

const G = 'git';
const F = '--' + 'force';
// [command, rule ids expected to fire ('' = none of G-002/G-004)]
const cases = [
  [`${G} push origin main`, ''],
  [`${G} push origin HEAD:main`, ''],
  [`${G} push origin refs/heads/main:refs/heads/main`, ''],
  [`${G} merge --no-ff feat/x -m "into main"`, ''],
  [`${G} merge --ff-only origin/main`, ''],
  [`${G} pull --ff-only origin main`, ''],
  [`${G} commit -m "fix the main loop"`, ''],
  [`${G} merge-base origin/main HEAD`, ''],
  [`${G} rebase origin/main`, 'G-004'],
  [`${G} rebase -i main`, 'G-004'],
  [`${G} push origin +main`, 'G-004'],
  [`${G} push origin +HEAD:main`, 'G-004'],
  [`${G} push origin :main`, 'G-004'],
  [`${G} push origin --delete main`, 'G-004'],
  [`${G} push -d origin release`, 'G-004'],
  [`${G} push ${F} origin main`, 'G-002'],
];

const patched = fs.readFileSync(path.join(CACHE, version, 'lib/control/destructive-detector.js'), 'utf8')
  .includes('bkit-g004-protected-branch-precision');
let bad = 0;
for (const [cmd, want] of cases) {
  const ids = ((detect('Bash', { command: cmd }) || {}).rules || []).map((r) => r.id).filter((id) => id === 'G-002' || id === 'G-004');
  const got = ids.join(',');
  const ok = want === '' ? got === '' : ids.includes(want);
  if (!ok) bad += 1;
  console.log(`${ok ? 'ok  ' : 'FAIL'} ${(got || 'clean').padEnd(13)} ${cmd}`);
}
console.log(`bkit ${version} — local patch ${patched ? 'PRESENT' : 'MISSING'} — ${cases.length - bad}/${cases.length} cases correct`);
console.log(bad === 0 ? 'RESULT: OK' : 'RESULT: FAIL — re-apply (README.md)');
process.exit(bad === 0 ? 0 : 1);
