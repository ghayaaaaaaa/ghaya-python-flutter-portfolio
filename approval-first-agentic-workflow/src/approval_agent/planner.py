from __future__ import annotations

from .models import Plan, Step


class DemoPlanner:
    """Build a fixed, inspectable plan for the bundled opportunity example."""

    def plan(self, goal: str) -> Plan:
        normalized = " ".join(goal.split())
        if not normalized:
            raise ValueError("A non-empty goal is required.")
        if not any(word in normalized.lower() for word in ("summar", "report")):
            raise ValueError(
                "This demonstration planner only handles summaries of its bundled examples."
            )

        return Plan(
            goal=normalized,
            steps=(
                Step(
                    step_id="load-examples",
                    tool="load_sample_opportunities",
                    arguments={},
                ),
                Step(
                    step_id="summarize-examples",
                    tool="summarize_opportunities",
                    arguments={"source": {"$step_result": "load-examples"}},
                ),
                Step(
                    step_id="write-summary",
                    tool="write_summary",
                    arguments={
                        "summary": {"$step_result": "summarize-examples"},
                        "destination": "reports/opportunities-summary.md",
                    },
                    requires_approval=True,
                ),
            ),
        )

