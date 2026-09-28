"""Task 11 item 11 (design D6 re-measure): wall time of `h_mad_tdd_judge.judge` on a real target.

Usage: judge_latency.py HEMASUITE_ROOT   (run from the skills worktree root)

HemaSuite is only READ. The snapshot follows `v1-offline-replay.sh`: `git archive` of
`hematology-paper-writer` and `shared` at 31bfcfe4 (Task 7's GREEN commit), that commit's
impl-plan, a synthesized step5 state at the root and an empty one in the sub-project, and an APFS
clone (`cp -c`) of the sub-project's `.venv`. At GREEN all four Task 7 candidates pass, so the
judge runs every one of them and never exits early on a RED: the worst case for the budget.

`judge` is imported and timed in-process, so interpreter start-up is not in the reading.
Prints `LATENCY: runs=3 worst_s=N budget_s=40.0`. Pass: `worst_s` below `budget_s`.
"""
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

GREEN_SHA = "31bfcfe4"
SUB = "hematology-paper-writer"
PLAN = "docs/01-plan/features/review-manifest-guideline-evidence.impl-plan.md"
PROD = "tools/review_round/guideline_excerpts.py"
RUNS = 3


def sh(argv, input=None, **kw):
    if input is None:
        kw["stdin"] = subprocess.DEVNULL
    return subprocess.run(argv, check=True, input=input, timeout=600.0, **kw)


def snapshot(hemasuite: Path, root: Path) -> None:
    (root / "docs/01-plan/features").mkdir(parents=True)
    archive = sh(["git", "-C", str(hemasuite), "archive", GREEN_SHA, SUB, "shared"],
                 capture_output=True).stdout
    sh(["tar", "-x", "-C", str(root)], input=archive)
    plan = sh(["git", "-C", str(hemasuite), "show", f"{GREEN_SHA}:{PLAN}"], capture_output=True).stdout
    (root / PLAN).write_bytes(plan)
    (root / "docs/.bkit-memory.json").write_text(json.dumps(
        {"orchestrator_state": {"review-manifest-guideline-evidence": {"phase": "step5"}}}) + "\n")
    (root / SUB / "docs").mkdir(exist_ok=True)
    (root / SUB / "docs/.bkit-memory.json").write_text('{"orchestrator_state":{}}\n')
    sh(["cp", "-cR", str(hemasuite / SUB / ".venv"), str(root / SUB / ".venv")])
    sh(["git", "init", "-q", str(root)])


def main() -> int:
    hemasuite = Path(sys.argv[1]).resolve()
    sys.path.insert(0, str(Path.cwd() / "h-mad" / "scripts"))
    import h_mad_tdd_judge as tj

    with tempfile.TemporaryDirectory(prefix="hmad-latency.") as tmp:
        root = Path(tmp).resolve()
        snapshot(hemasuite, root)
        target = root / SUB / PROD
        chain = tj.read_chain(root, target)
        if chain.value != "active":
            print(f"LATENCY: HALT chain={chain.value}")
            return 1
        times = []
        for n in range(RUNS):
            start = time.monotonic()
            verdict = tj.judge(root, target, chain.records)
            elapsed = time.monotonic() - start
            times.append(elapsed)
            print(f"LATENCY: run={n + 1} s={elapsed:.2f} verdict={verdict.decision} kind={verdict.kind}")
    worst = max(times)
    print(f"LATENCY: runs={RUNS} worst_s={worst:.2f} budget_s={tj.JUDGE_BUDGET_S}")
    return 0 if worst < tj.JUDGE_BUDGET_S else 2


if __name__ == "__main__":
    sys.exit(main())
