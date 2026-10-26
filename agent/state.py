"""Filesystem state helpers. Each artifact is atomically replaced after completion."""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
RUNS = ROOT / "sandbox" / "runs"
OUTPUT = ROOT / "output"


def scenario_id(scenario: str) -> str:
    """Purpose: Give each distinct problem its own persistent run folder.

    Input: The user's scenario text.
    Output: A readable slug followed by a short SHA-256 identifier.
    What it does: Normalizes whitespace/case so the same prompt resumes the same run.
    """
    digest = hashlib.sha256(" ".join(scenario.casefold().split()).encode("utf-8")).hexdigest()[:12]
    slug = re.sub(r"[^a-z0-9]+", "-", scenario.casefold()).strip("-")[:32] or "scenario"
    return f"{slug}-{digest}"


def timestamp() -> str:
    """Purpose: Create a consistent UTC timestamp for saved state.

    Input: None.
    Output: An ISO-formatted UTC timestamp string.
    What it does: Makes update times unambiguous across machines.
    """
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def atomic_json(path: Path, value: Any) -> None:
    """Purpose: Save a JSON artifact without leaving a half-written file.

    Input: Destination path and a JSON-serializable Python value.
    Output: None; creates or replaces the destination file.
    What it does: Writes a temporary file, flushes it, then atomically renames it.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def read_json(path: Path, default: Any = None) -> Any:
    """Purpose: Read a saved JSON file without crashing on missing/corrupt data.

    Input: File path and a value to return if reading fails.
    Output: Parsed JSON content or the provided default.
    What it does: Treats missing and malformed artifacts as unavailable.
    """
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def load_or_create(run_dir: Path, scenario: str, run_id: str) -> dict:
    """Purpose: Load progress for this scenario or create initial run state.

    Input: Run folder, original scenario text, and its scenario identifier.
    Output: A state dictionary ready for the workflow.
    What it does: Reuses matching saved progress and prevents cross-scenario mixing.
    """
    state_path = run_dir / "state" / "run_state.json"
    state = read_json(state_path, {})
    if not isinstance(state, dict) or state.get("scenario_id") != run_id:
        state = {
            "run_id": run_id,
            "scenario": scenario,
            "scenario_id": run_id,
            "status": "in_progress",
            "completed_stages": [],
            "created_at": timestamp(),
        }
    state["last_updated"] = timestamp()
    return state


def save_state(run_dir: Path, state: dict) -> None:
    """Purpose: Persist the current workflow progress.

    Input: Run folder and mutable state dictionary.
    Output: None; atomically updates state/run_state.json.
    What it does: Adds an update timestamp and writes the state to disk.
    """
    state["last_updated"] = timestamp()
    atomic_json(run_dir / "state" / "run_state.json", state)
