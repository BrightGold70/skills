"""Source-only loading for the Grok audit surface probe."""

import sys
import types
from pathlib import Path


def load_probe(path: Path) -> types.ModuleType:
    """Compile fresh source so same-size mutations cannot reuse stale bytecode."""
    code = compile(path.read_bytes(), str(path), "exec")
    module = types.ModuleType("grok_audit_probe")
    module.__file__ = str(path)
    sys.modules[module.__name__] = module
    exec(code, module.__dict__)
    return module
