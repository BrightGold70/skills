#!/usr/bin/env node
// Verify SubagentStop on the newest installed bkit. The local patch is RETIRED (bkit
// 2.1.41 fixed #162); this now checks that upstream still does not re-wake subagents.
// Exit 0: the handler still composes its next-action hint, and does not return it as
// additionalContext (which Claude Code delivers to the stopped subagent as a new turn).
// Exit 1: upstream regressed — re-apply the retired patch (README.md) and re-report. Exit 2: the check could not run — not a verdict.
//
// It drives the real handler as a subprocess against a throwaway project whose bkit
// state has a primary feature in phase `do`, so a hint IS generated. Without that
// positive control, "no additionalContext" would also pass when no hint existed at all.
'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');

const REL = 'scripts/subagent-stop-handler.js';
const MARKER = 'bkit-subagentstop-additionalcontext';
const CACHE = path.join(process.env.HOME, '.claude/plugins/cache/bkit-marketplace/bkit');
const versions = fs.readdirSync(CACHE)
  .filter((v) => fs.existsSync(path.join(CACHE, v, REL)))
  .sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));
if (versions.length === 0) { console.log('no bkit install found'); process.exit(2); }
const version = process.argv[2] || versions[versions.length - 1];
const handler = path.join(CACHE, version, REL);

const project = fs.mkdtempSync(path.join(os.tmpdir(), 'bkit-subagentstop-verify-'));
const FEATURE = 'verify-probe';
fs.mkdirSync(path.join(project, '.bkit/state'), { recursive: true });
fs.writeFileSync(path.join(project, '.bkit/state/pdca-status.json'), JSON.stringify({
  version: '2.0',
  primaryFeature: FEATURE,
  activeFeatures: [FEATURE],
  features: { [FEATURE]: { phase: 'do' } },
}));

const payload = {
  hook_event_name: 'SubagentStop',
  stop_hook_active: false,
  session_id: 'verify',
  agent_id: 'verify-agent',
  agent_type: 'spec-author',
  last_assistant_message: 'SPEC-AUTHOR: DONE',
};
const run = spawnSync('node', [handler], {
  input: JSON.stringify(payload),
  env: { ...process.env, CLAUDE_PROJECT_DIR: project },
  encoding: 'utf8',
  timeout: 15000,
});
fs.rmSync(project, { recursive: true, force: true });

const line = (run.stdout || '').trim().split('\n').filter(Boolean).pop() || '';
let out;
try { out = JSON.parse(line); } catch (_) {
  console.log(`could not parse handler output (status ${run.status}): ${line.slice(0, 200)}`);
  console.log((run.stderr || '').slice(0, 400));
  console.log('RESULT: CANNOT JUDGE');
  process.exit(2);
}

const hint = `/pdca analyze ${FEATURE}`;
const checks = [
  ['handler still composes the hint (control)', (out.systemMessage || '').includes(hint)],
  ['hint is not returned as additionalContext', !(out.hookSpecificOutput && 'additionalContext' in out.hookSpecificOutput)],
];
let bad = 0;
for (const [name, ok] of checks) {
  if (!ok) bad += 1;
  console.log(`${ok ? 'ok  ' : 'FAIL'} ${name}`);
}
const patched = fs.readFileSync(handler, 'utf8').includes(MARKER);
console.log(`bkit ${version} — local patch ${patched ? 'PRESENT' : 'MISSING'} — ${checks.length - bad}/${checks.length} checks correct`);
if (!checks[0][1]) {
  console.log('RESULT: CANNOT JUDGE — no hint was generated, so its absence proves nothing');
  process.exit(2);
}
console.log(bad === 0 ? 'RESULT: OK' : 'RESULT: FAIL — re-apply (README.md)');
process.exit(bad === 0 ? 0 : 1);
