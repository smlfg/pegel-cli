"""Lokaler Watch-Zustand unter dem XDG-State-Verzeichnis."""

from __future__ import annotations

import json
import os
from pathlib import Path


def state_dir() -> Path:
    raw = os.environ.get("XDG_STATE_HOME", "").strip()
    base = Path(raw) if raw else Path.home() / ".local" / "state"
    path = base / "pegel-cli"
    path.mkdir(parents=True, exist_ok=True)
    try:
        path.chmod(0o700)
    except OSError:
        pass
    return path


def state_path() -> Path:
    return state_dir() / "watch.json"


def load() -> dict[str, object]:
    try:
        data = json.loads(state_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(data, dict):
        return {}
    return data


def save(data: dict[str, object]) -> None:
    path = state_path()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass
