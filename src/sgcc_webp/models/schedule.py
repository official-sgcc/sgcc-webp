from pydantic import BaseModel
from sqlmodel import SQLModel, Field, Relationship
from typing import Any, TYPE_CHECKING
from uuid import UUID, uuid4
from datetime import datetime

if TYPE_CHECKING:
    from .group import Group

class BaseResponse(BaseModel):
    error: str = ""
    code: int = 200
    data: Any

class ScheduleBase(SQLModel):
    start_date: datetime            #시작 시간
    end_date: datetime              #종료 시간
    info: str | None = None         #일정 설명

class Schedule(ScheduleBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    group: "Group" = Relationship(back_populates="schedules")
    group_id: UUID = Field(foreign_key="group.id", index=True)

class SchedulePublic(ScheduleBase):
    id: UUID

class SchedulePost(ScheduleBase):
    group_id: UUID | None = None

class ScheduleList(BaseResponse):
    data: list[SchedulePublic]

class ScheduleResponse(BaseResponse):
    data: SchedulePublic