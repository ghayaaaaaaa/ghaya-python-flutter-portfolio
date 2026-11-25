from __future__ import annotations

import json
import uuid
from typing import Any

from .models import Plan, plan_to_dict
from .planner import DemoPlanner
from .store import StateStore
from .tools import TOOL_ALLOWLIST


def resolve_references(value: Any, results: dict[str, dict[str, Any]]) -> Any:
    if isinstance(value, dict):
        if set(value) == {"$step_result"}:
            step_id = value["$step_result"]
            if step_id not in results:
                raise ValueError(f"Referenced step is not complete: {step_id}")
            return results[step_id]
        return {key: resolve_references(item, results) for key, item in value.items()}
    if isinstance(value, list):
        return [resolve_references(item, results) for item in value]
    return value


class WorkflowEngine:
    def __init__(self, store: StateStore, planner: DemoPlanner | None = None):
        self.store = store
        self.planner = planner or DemoPlanner()

    def start(self, goal: str) -> tuple[str, list[str]]:
        plan: Plan = self.planner.plan(goal)
        if not plan.steps:
            raise ValueError("The planner returned an empty plan.")
        if any(step.tool not in TOOL_ALLOWLIST for step in plan.steps):
            raise ValueError("The plan contains a tool outside the allowlist.")
        run_id = uuid.uuid4().hex[:12]
        steps = [
            {
                "step_id": step.step_id,
                "tool": step.tool,
                "arguments": step.arguments,
                "requires_approval": step.requires_approval,
            }
            for step in plan.steps
        ]
        self.store.create_run(run_id, plan.goal, steps)
        self._continue_run(run_id)
        return run_id, [f"{run_id}:{step['step_id']}" for step in steps]

    def approve(self, action_id: str) -> None:
        step = self.store.get_step(action_id)
        if step is None:
            raise KeyError("Unknown action ID.")
        if step["status"] == "completed":
            return
        step = self.store.mark_approved(action_id)
        self._execute(step)
        self._continue_run(step["run_id"])

    def reject(self, action_id: str) -> None:
        self.store.mark_rejected(action_id)

    def _continue_run(self, run_id: str) -> None:
        while True:
            if self.store.run_status(run_id) in {"failed", "rejected", "completed"}:
                return
            queued = self.store.queued_steps(run_id)
            if not queued:
                self.store.mark_run_complete(run_id)
                return
            step = queued[0]
            if step["requires_approval"] and step["approval"] != "approved":
                self.store.mark_pending(step["action_id"])
                return
            self._execute(step)

    def _execute(self, row: Any) -> None:
        if row["status"] == "completed":
            return
        tool = TOOL_ALLOWLIST.get(row["tool"])
        if tool is None:
            self.store.mark_failed(row["action_id"], "UnknownTool")
            return
        self.store.mark_started(row["action_id"])
        try:
            saved_arguments = json.loads(row["arguments_json"])
            results = self.store.completed_results(row["run_id"])
            arguments = resolve_references(saved_arguments, results)
            result = tool(arguments)
            self.store.mark_completed(row["action_id"], result)
        except Exception as exc:
            self.store.mark_failed(row["action_id"], type(exc).__name__)

