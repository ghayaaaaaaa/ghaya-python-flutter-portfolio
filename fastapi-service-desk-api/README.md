# Service Desk API Demo

A small, local FastAPI service for managing synthetic support tickets. It demonstrates typed request and response models, bounded search and pagination, parameterized SQLite queries, status updates, and generated OpenAPI documentation.

This AI-assisted portfolio demonstration was prepared for Ghaya. It is not a client delivery, a hosted service, or a claim of production deployment.

## Features

- Create, list, search, update the status of, and delete tickets.
- Validate request fields and reject unexpected fields.
- Restrict status and priority to documented values.
- Use parameterized SQLite queries and a configurable local database path.
- Use `.local/` as the ignored default database location. `SERVICE_DESK_DB_PATH` can override it and is not constrained to the project directory.
- Expose interactive API documentation at `/docs` and an OpenAPI schema at `/openapi.json`.
- Seed three fictional tickets for a repeatable demo.

## Run locally

Use Python 3.11 or newer.

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn service_desk_api.app:app --reload
```

In a second terminal, seed the local database:

```powershell
.\.venv\Scripts\python.exe -m service_desk_api.seed
```

Open `http://127.0.0.1:8000/docs` to explore the API.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Liveness response |
| `POST` | `/tickets` | Create a ticket; returns HTTP 201 |
| `GET` | `/tickets` | Filter by `status` or `search`; paginate with `limit` and `offset` |
| `GET` | `/tickets/{ticket_id}` | Retrieve one ticket |
| `PATCH` | `/tickets/{ticket_id}/status` | Change status to `open`, `in_progress`, or `closed` |
| `DELETE` | `/tickets/{ticket_id}` | Delete one ticket |

Example request:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/tickets -ContentType 'application/json' -Body '{"title":"Review import flow","description":"Check missing-field handling.","priority":"normal"}'
```

Filter examples:

```text
GET /tickets?status=open&limit=20&offset=0
GET /tickets?search=import
```

## Data and security notes

The example records are fictional. The API has no authentication, authorization, rate limiting, audit log, or deployment configuration. Do not expose it to the public internet or use it with real customer records. Keep any credentials out of source code; this demo does not require credentials or third-party services.

## Attribution

Prepared with AI assistance for Ghaya's portfolio. No machine-learning model was trained for this project.

## License

No open-source license is included with this portfolio sample.

