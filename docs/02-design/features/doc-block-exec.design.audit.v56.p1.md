## Summary
The design document is exceptionally thorough, demonstrating a high degree of adversarial consistency and a rigorous mapping to the specification. Edge cases across lifecycle boundaries (reservations, timeouts, zombie-group reaping, and cleanup verification) are explicitly handled and pinned by corresponding tests and mutations. The exact matching of 63 mutation rows, proper accounting of the `test_suite_floor_holds` tuple, and precise exception precedence highlight a robust architectural plan.

## Must-fix
None

## Should-fix
None

## Nit
- In the "API / Interface Changes" section, the document states "`__all__` names all seven," immediately following the list of the seven public functions. However, the module also defines two public dataclasses (`Block` and `RunResult`) which callers need for typing and data extraction. Consider exporting all nine names in `__all__` or clarifying that the count refers exclusively to the functions.
