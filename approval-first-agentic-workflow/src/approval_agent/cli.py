from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Sequence

from .engine import WorkflowEngine, resolve_references
from .store import StateStore


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="approval-agent",
        description="Run a local workflow with allowlisted tools and explicit approval.",
    )
    parser.add_argument(
        "--state",
        type=Path,
        default=Path(".agent/state.sqlite3"),
        help="Path to the local SQLite state file.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    demo = commands.add_parser("demo", help="Start the bundled synthetic demonstration.")
    demo.set_defaults(command="demo")
    run = commands.add_parser("run", help="Plan and run the bundled opportunity summary.")
    run.add_argument("--goal", required=True, help="A concise description of the requested workflow.")
    pending = commands.add_parser("pending", help="List actions waiting for approval.")
    pending.set_defaults(command="pending")
    approve = commands.add_parser("approve", help="Approve and resume one pending action.")
    approve.add_argument("action_id")
    reject = commands.add_parser("reject", help="Reject one pending action.")
    reject.add_argument("action_id")
    return parser


def _pending_preview(row: sqlite3.Row, store: StateStore) -> str:
    arguments = json.loads(row["arguments_json"])
    resolved = resolve_references(arguments, store.completed_results(row["run_id"]))
    lines = [
        f"Action: {row['action_id']}",
        f"Goal: {row['goal']}",
        f"Tool: {row['tool']}",
    ]

    if row["tool"] == "write_summary":
        summary = resolved.get("summary", {})
        lines.extend(
            [
                f"Effect: Write a Markdown report to {resolved.get('destination', '(unknown destination)')}.",
                "Overwrite behavior: Existing files are never replaced.",
                "Exact report content:",
                str(summary.get("markdown", "(no report content available)")),
            ]
        )
    else:
        lines.append("Resolved arguments:")
        lines.append(json.dumps(resolved, ensure_ascii=False, indent=2, sort_keys=True))
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    store = StateStore(args.state)
    engine = WorkflowEngine(store)

    if args.command in {"demo", "run"}:
        goal = (
            "Summarize the bundled synthetic opportunity examples and prepare a local report."
            if args.command == "demo"
            else args.goal
        )
        run_id, action_ids = engine.start(goal)
        print(f"Run: {run_id}")
        print("Planned actions:")
        for action_id in action_ids:
            row = store.get_step(action_id)
            print(f"- {action_id} | {row['tool']} | {row['status']}")
        pending_rows = [row for row in store.pending_actions() if row["run_id"] == run_id]
        if pending_rows:
            print(f"Approval required: {pending_rows[0]['action_id']}")
            print("Inspect the exact pending action with: python -m approval_agent pending")
        return 0

    if args.command == "pending":
        rows = store.pending_actions()
        if not rows:
            print("No actions are waiting for approval.")
            return 0
        for row in rows:
            print(_pending_preview(row, store))
            print()
        return 0

    if args.command == "approve":
        row = store.get_step(args.action_id)
        if row is None:
            print("Unknown action ID.", file=sys.stderr)
            return 2
        if row["status"] == "pending" and row["requires_approval"]:
            print(_pending_preview(row, store))
            try:
                confirmation = input("Type approve to execute this exact action: ").strip()
            except EOFError:
                print("Approval requires an interactive terminal.", file=sys.stderr)
                return 2
            if confirmation != "approve":
                print("No action was executed.")
                return 0
        engine.approve(args.action_id)
        row = store.get_step(args.action_id)
        print(f"Action status: {row['status']}")
        if row["result_json"]:
            print(json.dumps(json.loads(row["result_json"]), ensure_ascii=False, indent=2))
        return 0

    if args.command == "reject":
        engine.reject(args.action_id)
        print("Action rejected; no report was written.")
        return 0

    return 2

