## Summary
The design provides a robust, heavily mutation-tested execution harness for markdown bash blocks, enforcing strict time bounds, secure temporary directories, and reliable artifact management. However, there is a gap in the mutation plan regarding the regular-file verification of stream artifacts.

## Must-fix
- `nonregular-stream-accepted` mutation survives its killer test — `test_stream_path_fifo_without_reader_refuses_bounded` cannot kill the removal of the `S_ISREG` check because a reader-less FIFO opened with `O_WRONLY | O_NONBLOCK` fails immediately at `os.open` with `ENXIO`. Since `open` fails, the execution never reaches the mutated `fstat` check, so the mutant behaves identically to the correct code (refusing with `StreamPathUnwritable`) and survives. To kill this mutant, the suite must test a non-regular file that *successfully* opens (e.g., `/dev/null`, or a FIFO with a reader) so the `fstat` check is actually reached.

## Should-fix
None

## Nit
- Stale `arg=` in the CLI empty key description — The spec states that for an empty `--subst` key, "the verdict prints `arg=` instead of the raw `arg==V`". However, since design v70 routes all dynamic fields through `_field` which applies `json.dumps(str(value))`, an empty string `raw` parameter would render as `arg=""`, not a bare `arg=`.
