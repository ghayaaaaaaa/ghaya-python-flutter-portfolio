from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Step:
    step_id: str
    tool: str
    arguments: dict[str, Any]
    requires_approval: bool = False


@dataclass(frozen=True)
class Plan:
    goal: str
    steps: tuple[Step, ...]


def plan_to_dict(plan: Plan) -> dict[str, Any]:
    return {
        "goal": plan.goal,
        "steps": [asdict(step) for step in plan.steps],
    }

