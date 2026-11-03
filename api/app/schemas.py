from __future__ import annotations

from typing import Any

from pydantic import BaseModel, field_validator

DEFAULT_STATUS = "TODO"
DEFAULT_PRIORITY = "MEDIUM"


class NewTaskPayload(BaseModel):
    title: str = ""
    description: str = ""
    status: str = DEFAULT_STATUS
    priority: str = DEFAULT_PRIORITY
    owner: str | None = None

    @field_validator("title", "description", "status", "priority", "owner", mode="before")
    @classmethod
    def coerce_to_text(cls, value: Any) -> str:
        return str(value)
