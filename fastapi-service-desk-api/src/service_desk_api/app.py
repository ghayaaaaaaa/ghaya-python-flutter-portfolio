from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query, Response, status

from .database import initialize_database
from .repository import create_ticket, delete_ticket, get_ticket, list_tickets, update_ticket_status
from .schemas import DeleteResult, TicketCreate, TicketList, TicketOut, TicketStatus, TicketStatusUpdate


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="Service Desk API Demo",
    description=(
        "A local FastAPI and SQLite demonstration for creating, filtering, and updating "
        "synthetic service tickets. It has no authentication and is not intended for real customer data."
    ),
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/tickets", response_model=TicketOut, status_code=status.HTTP_201_CREATED, tags=["tickets"])
def create(payload: TicketCreate) -> TicketOut:
    return create_ticket(payload)


@app.get("/tickets", response_model=TicketList, tags=["tickets"])
def list_all(
    status_filter: Annotated[TicketStatus | None, Query(alias="status")] = None,
    search: Annotated[str | None, Query(min_length=1, max_length=80)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> TicketList:
    items, total = list_tickets(status=status_filter, search=search, limit=limit, offset=offset)
    return TicketList(items=list(items), limit=limit, offset=offset, total=total)


@app.get("/tickets/{ticket_id}", response_model=TicketOut, tags=["tickets"])
def get_one(ticket_id: int) -> TicketOut:
    ticket = get_ticket(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found.")
    return ticket


@app.patch("/tickets/{ticket_id}/status", response_model=TicketOut, tags=["tickets"])
def change_status(ticket_id: int, payload: TicketStatusUpdate) -> TicketOut:
    ticket = update_ticket_status(ticket_id, payload.status)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found.")
    return ticket


@app.delete("/tickets/{ticket_id}", response_model=DeleteResult, tags=["tickets"])
def remove(ticket_id: int, response: Response) -> DeleteResult:
    deleted = delete_ticket(ticket_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found.")
    response.status_code = status.HTTP_200_OK
    return DeleteResult(deleted=True, id=ticket_id)
