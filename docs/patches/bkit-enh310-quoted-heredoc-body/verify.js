#!/usr/bin/env node
// Self-contained verifier for bkit ENH-310 quoted-heredoc-body behaviour.
//
// The local patch is RETIRED: upstream fixed bkit#145 in v2.1.34, and the
// local patch was dropped on 2026-10-18 at bkit 2.1.40. Run AFTER any bkit
// plugin update to check the upstream detector against the same cases:
//   node docs/patches/bkit-enh310-quoted-heredoc-body/verify.js
//
// Exit 0 = every case correct, except the KNOWN_GAPS upstream has not closed.
// Exit 1 = a case outside KNOWN_GAPS failed — the guard regressed upstream.
//
// Absolute expectations — deliberately does NOT diff against a saved original,
// so it keeps working across bkit versions.

const path = require('node:path');

const CACHE = path.join(
  process.env.HOME,
  '.claude/plugins/cache/bkit-marketplace/bkit'
);

function resolveDetector() {
  const fs = require('node:fs');
  if (!fs.existsSync(CACHE)) return null;
  // Pick the highest installed version directory.
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
  const p = path.join(CACHE, v, 'lib/defense/heredoc-detector.js');
  return fs.existsSync(p) ? { version: v, path: p } : null;
}

const found = resolveDetector();
if (!found) {
  console.log('SKIP — bkit heredoc-detector not found; nothing to verify.');
  process.exit(0);
}

const det = require(found.path);
const D = '$';

// [name, command, expectation] — 'not-critical' | 'critical'
const CASES = [
  // The false positive this patch fixes.
  ['prose-in-quoted-body',
    `python3 - <<'PY'\ns = "${D}(cat <<'EOF' ... EOF)"\nPY`, 'not-critical'],
  ['terminator-lookalike',
    `python3 - <<'PY'\n  PY_NOT_REALLY\n${D}(cat <<EOF\nx\nEOF\n)\nPY`, 'not-critical'],

  // The guard must still bite on all of these.
  ['genuine-sub-quoted-tag',
    `git commit -m "${D}(cat <<'EOF'\nbody\nEOF\n)"`, 'critical'],
  ['genuine-sub-bare-tag',
    `echo "${D}(cat <<EOF\nbody\nEOF\n)"`, 'critical'],
  ['bare-outer-quoted-inner',
    `cat <<OUTER\n${D}(cat <<'IN'\nx\nIN\n)\nOUTER`, 'critical'],
  ['pipe-to-bash',
    "cat <<'EOF' | bash\nrm -rf /\nEOF", 'critical'],
  ['quoted-body-piped-bash',
    "python3 - <<'PY' | bash\nprint('rm -rf /')\nPY", 'critical'],
  ['pipe-to-sudo',
    "cat <<'T'\nrm /\nT\n| sudo", 'critical'],
  ['unterminated-fail-safe',
    `python3 - <<'PY'\n${D}(cat <<EOF\nnever closed`, 'critical'],
];

// Cases the upstream fix (v2.1.34+) still gets wrong. Accepted when the local
// patch was retired; see docs/skill-monitoring.md. Remove an entry once
// upstream closes it — this script says when.
const KNOWN_GAPS = new Set(['terminator-lookalike']);

let bad = 0;
let gaps = 0;

for (const [name, cmd, expect] of CASES) {
  const sev = det.detect(cmd).severity;
  const ok = expect === 'critical' ? sev === 'critical' : sev !== 'critical';
  if (ok && KNOWN_GAPS.has(name)) {
    console.log(`  GAP CLOSED ${name}: upstream now gets this right — remove it from KNOWN_GAPS`);
  } else if (!ok && KNOWN_GAPS.has(name)) {
    gaps++;
    console.log(`  known gap ${name}: expected ${expect}, got severity=${sev}`);
  } else if (!ok) {
    bad++;
    console.log(`  FAIL ${name}: expected ${expect}, got severity=${sev}`);
  }
}

console.log(`bkit ${found.version} — ${CASES.length - bad - gaps}/${CASES.length} cases correct, ${gaps} known gap(s)`);

if (bad > 0) {
  console.log('RESULT: FAIL — upstream guard behaviour regressed outside the known gaps');
  process.exit(1);
}
console.log('RESULT: OK — upstream behaviour matches, apart from the known gaps');
process.exit(0);
