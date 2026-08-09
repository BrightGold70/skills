#!/usr/bin/env node
// Self-contained verifier for the bkit ENH-310 quoted-heredoc-body patch.
//
// Run AFTER any bkit plugin update to check whether the patch is still applied:
//   node docs/patches/bkit-enh310-quoted-heredoc-body/verify.js
//
// Exit 0 = patch present and the guard is still intact.
// Exit 1 = patch missing (re-apply) or, worse, the guard was widened.
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

let bad = 0;
const patchPresent = typeof det.stripQuotedHeredocBodies === 'function';

for (const [name, cmd, expect] of CASES) {
  const sev = det.detect(cmd).severity;
  const ok = expect === 'critical' ? sev === 'critical' : sev !== 'critical';
  if (!ok) {
    bad++;
    console.log(`  FAIL ${name}: expected ${expect}, got severity=${sev}`);
  }
}

console.log(`bkit ${found.version} — patch symbol ${patchPresent ? 'PRESENT' : 'MISSING'}, ${CASES.length - bad}/${CASES.length} cases correct`);

if (bad > 0 && !patchPresent) {
  console.log('RESULT: patch NOT applied — re-apply heredoc-detector.patch (see README.md)');
  process.exit(1);
}
if (bad > 0) {
  console.log('RESULT: FAIL — guard behaviour is wrong even though the patch symbol is present');
  process.exit(1);
}
console.log('RESULT: OK — false positive fixed, guard still intact');
process.exit(0);
