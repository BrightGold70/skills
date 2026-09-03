## Summary
The implementation plan perfectly translates the design into exact module-level code structures, correctly mapped exceptions, and comprehensive mutation logic. The tasks are correctly split between wiring and new-behaviour shapes, and the wire-pin scaffolds are robust. The plan meets all audit criteria with high fidelity.

## Must-fix
None

## Should-fix
None

## Nit
- The plan uses `os.path` for `docsections.py`'s `sys.path.insert` (`os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts")`), whereas the design explicitly prescribes `str(Path(__file__).resolve().parents[1] / "scripts")`. They are functionally equivalent, but using the prescribed snippet avoids drift.
