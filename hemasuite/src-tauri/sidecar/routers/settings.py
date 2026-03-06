"""Settings API router — read/write HemaSuite app configuration."""

import json
import os
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/settings", tags=["settings"])

DEFAULTS = {
    "r_path": "Rscript",
    "python_path": "python3",
    "output_dir": "~/HemaSuite/output",
    "theme": "light",
    "default_journal": "",
}


def _config_path() -> Path:
    base = os.environ.get(
        "HEMASUITE_CONFIG_DIR",
        str(Path.home() / "HemaSuite"),
    )
    return Path(base) / "settings.json"


def _read_settings() -> dict:
    path = _config_path()
    settings = {**DEFAULTS}
    if path.exists():
        with open(path) as f:
            saved = json.load(f)
        settings.update(saved)
    return settings


def _write_settings(settings: dict) -> None:
    path = _config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(settings, f, indent=2)


@router.get("")
async def get_settings():
    return _read_settings()


@router.patch("")
async def update_settings(updates: dict):
    settings = _read_settings()
    settings.update(updates)
    _write_settings(settings)
    return settings
