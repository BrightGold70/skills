"""
CLIRunner: converts Streamlit widget values to HPW CLI argument lists.
"""

import sys
from pathlib import Path
from typing import Any

# cli.py lives at hematology-paper-writer/cli.py; ui/ is one level below
_CLI_PATH = Path(__file__).parent.parent / "cli.py"
HPW_CLI = [sys.executable, str(_CLI_PATH)]


def build_hpw_args(command: str, widget_values: dict[str, Any]) -> list[str]:
    """
    Build a complete HPW CLI invocation from a phase command + widget state dict.

    Key conventions:
    - Keys starting with "--" are flags: True → bare flag, str/int → flag + value
    - Keys without "--" are positional arguments (appended before flags)
    - None, "", False values are skipped

    Example:
      build_hpw_args("create-draft", {
          "topic": "Asciminib CML review",
          "--journal": "blood_research",
          "--docx": True,
          "--max-results": 50,
          "--verify-references": False,
      })
      → [python, cli.py, "create-draft", "Asciminib CML review",
         "--journal", "blood_research", "--docx", "--max-results", "50"]
    """
    cmd = list(HPW_CLI) + [command]
    positionals: list[str] = []
    flags: list[str] = []

    for key, val in widget_values.items():
        if val is None or val == "" or val is False:
            continue
        if not key.startswith("--"):
            positionals.append(str(val))
        elif val is True:
            flags.append(key)
        else:
            flags.extend([key, str(val)])

    return cmd + positionals + flags
