from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

TicketPriority = Literal["low", "normal", "high"]
TicketStatus = Literal["open", "in_progress", "closed"]


class TicketCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(min_length=3, max_length=120)
    description: str = Field(default="", max_length=2000)
    priority: TicketPriority = "normal"


class TicketStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    status: TicketStatus


class TicketOut(BaseModel):
    id: int
    title: str
    description: str
    priority: TicketPriority
    status: TicketStatus
    created_at: str
    updated_at: str


class TicketList(BaseModel):
    items: list[TicketOut]
    limit: int
    offset: int
    total: int


class DeleteResult(BaseModel):
    deleted: bool
    id: int
