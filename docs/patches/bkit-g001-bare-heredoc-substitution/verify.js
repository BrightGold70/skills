#!/usr/bin/env node
// Self-contained verifier for bkit's destructive-detector heredoc handling.
//
// Run AFTER any bkit plugin update:
//   node docs/patches/bkit-g001-bare-heredoc-substitution/verify.js
//
// Exit 0 = every case correct, except the KNOWN_GAPS upstream has not closed.
// Exit 1 = a case outside KNOWN_GAPS failed. If the patch marker reads MISSING,
//          the update dropped the local patch: re-apply it (see README.md).
//
// Absolute expectations — deliberately does NOT diff against a saved original,
// so it keeps working across bkit versions. Trigger tokens are built by
// concatenation so this file never trips the live hook when shown in a shell.

const fs = require('node:fs');
const path = require('node:path');

const CACHE = path.join(process.env.HOME, '.claude/plugins/cache/bkit-marketplace/bkit');
const MARKER = 'LOCAL PATCH (skills docs/patches/bkit-g001-bare-heredoc-substitution)';

function resolveDetector() {
  if (!fs.existsSync(CACHE)) return null;
  const versions = fs
    .readdirSync(CACHE)
    .filter((v) => /^\d+\.\d+\.\d+$/.test(v))
    .sort((a, b) => {
      const pa = a.split('.').map(Number);
      const pb = b.split('.').map(Number);
      for (let i = 0; i < 3; i++) if (pa[i] !== pb[i]) return pa[i] - pb[i];
      return 0;
    });
  if (versions.length === 0) return null;
  const v = versions[versions.length - 1];
  const p = path.join(CACHE, v, 'lib/control/destructive-detector.js');
  return fs.existsSync(p) ? { version: v, path: p } : null;
}

const found = resolveDetector();
if (!found) {
  console.log('SKIP — bkit destructive-detector not found; nothing to verify.');
  process.exit(0);
}

const det = require(found.path);
const patched = fs.readFileSync(found.path, 'utf8').includes(MARKER);

const RMRF = 'rm' + ' -rf';
const RT = 'shutil.' + 'rm' + 'tree';
const sub = (inner) => '$' + '(' + inner + ')';

// [name, command, expectation] — 'clean' | 'detected' (any G-001) | 'critical'
const CASES = [
  // The false negative the local patch closes: bash expands these bodies.
  ['bare-body-sub-delete', `cat > /tmp/x <<EOF\n${sub(`${RMRF} ~`)}\nEOF`, 'detected'],
  ['bare-body-backtick-delete', `cat > /tmp/x <<EOF\n\`${RMRF} ~\`\nEOF`, 'detected'],
  ['bare-body-sub-python-delete',
    `cat > /tmp/x <<EOF\n${sub(`python3 -c "import shutil; ${RT}('/x')"`)}\nEOF`, 'detected'],

  // Upstream's v2.1.34+ false-positive fix must survive the patch.
  ['quoted-body-names-token', `cat > /tmp/p.txt <<'EOF'\nnever call ${RT} here\nEOF`, 'clean'],
  ['quoted-body-sub-is-inert', `cat > /tmp/x <<'EOF'\n${sub(`${RMRF} ~`)}\nEOF`, 'clean'],
  ['bare-body-plain-prose', `cat > /tmp/x <<EOF\nnever run ${RMRF} on home\nEOF`, 'clean'],

  // Controls: the guard must still bite.
  ['control-broad-delete', `${RMRF} ~`, 'critical'],
  ['control-real-python-delete', `python3 -c "import shutil; ${RT}('/')"`, 'critical'],
  ['control-scoped-delete-asks', `${RMRF} /tmp/scratch/build`, 'detected'],

  // Accepted gaps, tracked so this script reports when upstream closes them.
  ['commit-message-names-token', `git commit -m "stop calling ${RT} on the cache"`, 'clean'],
  ['sub-broad-delete-grades-critical', `echo ${sub(`${RMRF} ~`)}`, 'critical'],
];

// commit-message-names-token: a quoted string that only NAMES the token is
//   denied as critical. Not loosened locally — `python3 -c "…"` is the same
//   shape and real. Workaround: `git commit -F <file>`.
// sub-broad-delete-grades-critical: deleteTargetIsBroad() reads `~)` as one
//   operand, so a broad delete inside $() grades high/ask instead of deny.
const KNOWN_GAPS = new Set(['commit-message-names-token', 'sub-broad-delete-grades-critical']);

function classify(cmd) {
  const r = det.detect('Bash', { command: cmd });
  const g = (r.rules || []).filter((x) => x.id === 'G-001');
  if (g.length === 0) return 'clean';
  return g.some((x) => x.severity === 'critical') ? 'critical' : 'detected';
}

let bad = 0;
let gaps = 0;
for (const [name, cmd, expect] of CASES) {
  const got = classify(cmd);
  const ok = expect === 'detected' ? got !== 'clean' : got === expect;
  if (ok && KNOWN_GAPS.has(name)) {
    console.log(`  GAP CLOSED ${name}: upstream now gets this right — remove it from KNOWN_GAPS`);
  } else if (!ok && KNOWN_GAPS.has(name)) {
    gaps++;
    console.log(`  known gap ${name}: expected ${expect}, got ${got}`);
  } else if (!ok) {
    bad++;
    console.log(`  FAIL ${name}: expected ${expect}, got ${got}`);
  }
}

console.log(`bkit ${found.version} — local patch ${patched ? 'PRESENT' : 'MISSING'} — `
  + `${CASES.length - bad - gaps}/${CASES.length} cases correct, ${gaps} known gap(s)`);
if (bad > 0) {
  console.log(patched
    ? 'RESULT: FAIL — patched detector regressed; investigate before trusting the guard'
    : 'RESULT: FAIL — patch MISSING and upstream not fixed; re-apply (README.md)');
  process.exit(1);
}
console.log(patched
  ? 'RESULT: OK — patched detector behaves as expected, apart from the known gaps'
  : 'RESULT: OK — patch MISSING but upstream behaves correctly: drop the local patch');
process.exit(0);
