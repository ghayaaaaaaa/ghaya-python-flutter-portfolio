from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_ROOT = (PROJECT_ROOT / "reports").resolve()


def load_sample_opportunities(arguments: dict[str, Any]) -> dict[str, Any]:
    if arguments:
        raise ValueError("The sample loader accepts no caller-supplied paths.")
    sample_path = PROJECT_ROOT / "samples" / "opportunities.json"
    rows = json.loads(sample_path.read_text(encoding="utf-8"))
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise ValueError("The bundled example must be a JSON array of objects.")
    return {"rows": rows, "source": "bundled synthetic example"}


def summarize_opportunities(arguments: dict[str, Any]) -> dict[str, Any]:
    source = arguments.get("source")
    if not isinstance(source, dict) or not isinstance(source.get("rows"), list):
        raise ValueError("Expected rows from the sample-loading step.")
    rows = source["rows"]
    if not rows:
        return {
            "count": 0,
            "python_count": 0,
            "flutter_count": 0,
            "budget_total_usd": 0,
            "markdown": "No example opportunities were available.",
        }

    total = 0
    categories: dict[str, int] = {}
    for row in rows:
        budget = row.get("budget_usd")
        if not isinstance(budget, (int, float)) or isinstance(budget, bool):
            raise ValueError("Every example must have a numeric budget_usd value.")
        total += int(budget)
        category = str(row.get("category", "Other"))
        categories[category] = categories.get(category, 0) + 1

    titles = [str(row.get("title", "Untitled")) for row in rows]
    markdown = "\n".join(
        [
            "# Example Opportunity Summary",
            "",
            f"- Example records: {len(rows)}",
            f"- Combined example budget: USD {total:,}",
            f"- Python examples: {categories.get('Python', 0)}",
            f"- Flutter examples: {categories.get('Flutter', 0)}",
            "",
            "## Included examples",
            *[f"- {title}" for title in titles],
            "",
            "All records in this report are fictional demonstration data.",
        ]
    )
    return {
        "count": len(rows),
        "python_count": categories.get("Python", 0),
        "flutter_count": categories.get("Flutter", 0),
        "budget_total_usd": total,
        "markdown": markdown,
    }


def write_summary(arguments: dict[str, Any]) -> dict[str, Any]:
    summary = arguments.get("summary")
    destination = arguments.get("destination")
    if not isinstance(summary, dict) or not isinstance(summary.get("markdown"), str):
        raise ValueError("Expected a Markdown summary from the previous step.")
    if not isinstance(destination, str):
        raise ValueError("The destination must be a relative path.")

    output_path = (PROJECT_ROOT / destination).resolve()
    if (PROJECT_ROOT / "reports").is_symlink():
        raise ValueError("The reports directory cannot be a symlink.")
    if output_path.parent != REPORT_ROOT or output_path.suffix.lower() != ".md":
        raise ValueError("Reports can only be written as Markdown directly under reports/.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with output_path.open("x", encoding="utf-8", newline="\n") as report_file:
            report_file.write(summary["markdown"] + "\n")
    except FileExistsError as exc:
        raise FileExistsError(
            "The report already exists; rename it before approving another write."
        ) from exc
    return {"written_to": output_path.relative_to(PROJECT_ROOT).as_posix()}


Tool = Callable[[dict[str, Any]], dict[str, Any]]

TOOL_ALLOWLIST: dict[str, Tool] = {
    "load_sample_opportunities": load_sample_opportunities,
    "summarize_opportunities": summarize_opportunities,
    "write_summary": write_summary,
}

