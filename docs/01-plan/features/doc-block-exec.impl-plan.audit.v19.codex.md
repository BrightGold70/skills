## Summary
The plan is unusually concrete and keeps the scanner, wire, mutation, and transport contracts aligned. One Task 4 test path is internally impossible, so it cannot provide the promised escaping proof or mutation kill.

## Must-fix
- `test_newline_in_dynamic_fields_cannot_forge_a_verdict_line` case (3) requires `--stdout` to be under a regular-file parent (so the first reservation fails) and also requires a `leftover:` line — `leftover:` is specified only after a successful first reservation followed by failed second reservation and failed rollback unlink. On the stated first-arm `ENOTDIR` path no handle/file was created, so there is nothing to roll back or report as leftover; the test will fail against a correct implementation. Make the newline-bearing path the successfully-created stdout artifact and fail the stderr reservation under a regular file while injecting `os.unlink` (as AC-3.10 does), or assert escaped `os_error:` from the first-arm failure instead; update the design and the `field-escape-removed` mutation’s discriminator accordingly.

## Should-fix
None

## Nit
None
