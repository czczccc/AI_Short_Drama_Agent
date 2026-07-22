from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints


class StrictProjectModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProjectCreate(StrictProjectModel):
    name: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=200),
    ]


class ProjectRead(StrictProjectModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: int
    name: str
    status: str
    created_at: datetime
    updated_at: datetime
