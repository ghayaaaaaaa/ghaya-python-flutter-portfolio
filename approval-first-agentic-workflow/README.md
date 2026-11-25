# Approval-First Agentic Workflow

A small, local workflow agent that plans a bounded task, calls allowlisted tools, records each transition in SQLite, and pauses before a file-writing action until a person approves it.

This AI-assisted portfolio demonstration was prepared for Ghaya. It does not contain or train a machine-learning model, and the default planner does not call an LLM. The deterministic planner keeps the demonstration reproducible and offline. The project focuses on agent orchestration, controlled tool use, explicit approval, idempotent execution, and an audit trail.

## What it does

- Converts a narrow request into a three-step plan.
- Reads only the bundled, synthetic opportunity examples.
- Produces a compact summary from those examples.
- Requires a separate approval command before writing a Markdown report.
- Stores plans, step states, results, and audit events in a local SQLite database.
- Refuses unknown tools and file paths outside the project report directory.
- Does not make network requests or execute shell commands.

## Run the demonstration

Use Python 3.11 or newer. There are no third-party runtime dependencies.

From this directory:

    python -m pip install -e .
    python -m approval_agent demo

The command prints an action ID and leaves the final report step waiting for approval. Inspect the exact report and destination with:

    python -m approval_agent pending

To approve an action, run:

    python -m approval_agent approve ACTION_ID

The command displays the same action preview and requires you to type `approve`. The report writer refuses to replace an existing file; rename or remove the previous demo report before starting another write.

The approved report is written under `reports/`. The local database is stored under `.agent/` and is ignored by Git.

To start a new run:

    python -m approval_agent run --goal "Summarize the bundled opportunities and prepare a report"

Use --state PATH with any command to choose a different local SQLite file.

## Design notes

The planner emits typed steps rather than arbitrary code. The tool registry is an explicit allowlist. Tool arguments are resolved only from earlier step results or literal values. The write tool validates its destination, and a pending write cannot run until its action ID is approved. SQLite transactions record state transitions before execution, and a completed step is not run a second time when approval is repeated.

The example data is fictional and included only to make the workflow self-contained. It is not a set of current job listings or a claim about completed client work.

The local SQLite state stores the supplied goal, plan, results, and audit events without application-level encryption. Use synthetic or non-sensitive input only.

## Limitations

This is a demonstrator, not a hosted agent service. It has no user authentication, multi-tenant isolation, cloud deployment, external integrations, or LLM planner. SQLite is intended for a single local operator. Review code and permissions before adapting it to real business workflows.

## Portfolio attribution

Prepared with AI assistance for Ghaya's portfolio. The implementation does not claim that a model was trained. No private client information or credentials are included.

## License

No open-source license is included with this portfolio sample.


