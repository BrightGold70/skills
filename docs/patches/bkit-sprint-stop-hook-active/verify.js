#!/usr/bin/env node
// Verify the local sprint Stop-handler guard on the newest installed bkit.
// Exit 0: with an active sprint, a fresh stop still surfaces the summary (decision:block)
// and a stop with stop_hook_active=true does not. Exit 1: re-apply (README.md).
// Exit 2: the check could not run — not a verdict.
//
// It drives the real scripts/unified-stop.js (the only Stop hook in hooks.json) in a
// throwaway project with one active sprint. The stop_hook_active=false case is the
// positive control: without it, "no block" would also pass if sprint never surfaced.
'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');

const REL = 'scripts/sprint-skill-stop.js';
const MARKER = 'bkit-sprint-stop-hook-active';
const CACHE = path.join(process.env.HOME, '.claude/plugins/cache/bkit-marketplace/bkit');
const versions = fs.readdirSync(CACHE)
  .filter((v) => fs.existsSync(path.join(CACHE, v, REL)))
  .sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));
if (versions.length === 0) { console.log('no bkit install found'); process.exit(2); }
const version = process.argv[2] || versions[versions.length - 1];
const root = path.join(CACHE, version);

function stop(stopHookActive) {
  const proj = fs.mkdtempSync(path.join(os.tmpdir(), 'bkit-sprint-verify-'));
  fs.mkdirSync(path.join(proj, '.bkit/state/sprints'), { recursive: true });
  fs.writeFileSync(path.join(proj, '.bkit/state/sprints/verify.json'), JSON.stringify({
    id: 'verify', status: 'active', phase: 'do', phaseHistory: [{ phase: 'plan' }, { phase: 'do' }],
  }));
  const payload = {
    hook_event_name: 'Stop',
    stop_hook_active: stopHookActive,
    session_id: 'verify',
    skill_name: 'sprint',
    last_assistant_message: '/sprint phase verify done.',
  };
  const r = spawnSync('node', [path.join(root, 'scripts/unified-stop.js')], {
    input: JSON.stringify(payload),
    env: { ...process.env, CLAUDE_PROJECT_DIR: proj },
    cwd: proj,
    encoding: 'utf8',
    timeout: 20000,
  });
  fs.rmSync(proj, { recursive: true, force: true });
  const lines = (r.stdout || '').trim().split('\n').filter(Boolean);
  const parsed = [];
  for (const l of lines) { try { parsed.push(JSON.parse(l)); } catch (_) { /* non-JSON line */ } }
  return { status: r.status, blocked: parsed.some((o) => o && o.decision === 'block'), lines };
}

const fresh = stop(false);
const continued = stop(true);
const checks = [
  ['fresh stop with an active sprint still blocks (control)', fresh.blocked],
  ['stop with stop_hook_active=true does not block', !continued.blocked],
];
let bad = 0;
for (const [name, ok] of checks) {
  if (!ok) bad += 1;
  console.log(`${ok ? 'ok  ' : 'FAIL'} ${name}`);
}
const patched = fs.readFileSync(path.join(root, REL), 'utf8').includes(MARKER);
console.log(`bkit ${version} — local patch ${patched ? 'PRESENT' : 'MISSING'} — ${checks.length - bad}/${checks.length} checks correct`);
if (!fresh.blocked) {
  console.log(`RESULT: CANNOT JUDGE — the control did not block (exit ${fresh.status}, stdout ${JSON.stringify(fresh.lines).slice(0, 160)})`);
  process.exit(2);
}
console.log(bad === 0 ? 'RESULT: OK' : 'RESULT: FAIL — re-apply (README.md)');
process.exit(bad === 0 ? 0 : 1);
