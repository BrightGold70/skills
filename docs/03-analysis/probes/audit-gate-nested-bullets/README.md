# audit-gate nested bullets — probe evidence (2026-10-02)

- `corpus-differential.txt`: old gate (`9e1d21c4`) vs new over every committed audit report,
  each scored with its own `## Acknowledged-not-fixed` sidecar. 1047 scored, 10 changed (all with
  nested bullets), 0 verdict flips, 0 newly measurement-only musts.
- `fuzz.py` + `h.py` (written by the third fresh reviewer): random Must/Should sections and ack
  sets; tags any verdict flip (`V`), newly measurement-only musts (`MEAS`), lost ack refusals
  (`ACKREF`), or a count that rose (`UP`). Run from this directory after
  `git show 9e1d21c4:h-mad/scripts/h_mad_audit_gate.py > old_gate.py`:
  `python3 fuzz.py <seed> <n>`. Seeds 1-5 × 4000 on the final code: `done []`.
  Positive control: the same run against a copy with the NB-MEAS guard removed prints
  `done ['MEAS']`.
