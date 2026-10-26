"""CLI entry point. State is scoped to a normalized scenario hash and survives restarts."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from model import GroqClient, ModelError
from orchestration import run_workflow
from state import RUNS, load_or_create, save_state, scenario_id


def load_dotenv(path: Path) -> None:
    """Purpose: Load optional local settings from a .env file.

    Input: Path to the .env file.
    Output: None; missing values are added to the process environment.
    What it does: Keeps already-exported environment values and never prints secrets.
    """
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip().strip("\"'")
        if key and key not in os.environ:
            os.environ[key] = value


def main() -> int:
    """Purpose: Run the policy advisor from the command line.

    Input: Scenario text passed as command-line words.
    Output: Process exit code (0 complete, non-zero if interrupted or invalid).
    What it does: Loads settings/state, runs resumable stages, and reports the result.
    """
    parser = argparse.ArgumentParser(description="Resumable Road Safety Policy Advisor")
    parser.add_argument("scenario", nargs="+", help="Policy problem to investigate")
    args = parser.parse_args()
    scenario = " ".join(args.scenario).strip()
    if len(scenario) < 12:
        parser.error("Please provide a specific policy scenario (at least 12 characters).")
    load_dotenv(Path(__file__).resolve().parent / ".env")
    run_id = scenario_id(scenario)
    run_dir = RUNS / run_id
    state = load_or_create(run_dir, scenario, run_id)
    save_state(run_dir, state)
    try:
        client = GroqClient()
        report = run_workflow(client, run_dir, state)
        state.pop("last_error", None)
        save_state(run_dir, state)
    except ModelError as exc:
        state["status"] = "interrupted"
        safe_error = str(exc).replace(os.getenv("GROQ_API_KEY", "\0"), "[redacted]")
        state["last_error"] = safe_error
        save_state(run_dir, state)
        print(f"\nStopped safely: {safe_error}\nResume with the same scenario after resolving the API issue. Completed stages are saved under {run_dir}.", file=sys.stderr)
        return 2
    except (ValueError, KeyError, OSError) as exc:
        state["status"] = "interrupted"
        state["last_error"] = f"{type(exc).__name__}: {exc}"
        save_state(run_dir, state)
        print(f"\nStage could not be completed: {type(exc).__name__}: {exc}\nFix the issue and rerun the identical scenario; completed artifacts will be reused.", file=sys.stderr)
        return 3
    print(f"\nComplete. Decision report: {report}")
    print(f"Persistent run state: {run_dir / 'state' / 'run_state.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
