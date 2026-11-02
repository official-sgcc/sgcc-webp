from pydantic import BaseModel
from sqlmodel import SQLModel, Field
from typing import Any
from uuid import UUID, uuid4
from datetime import datetime

class BaseResponse(BaseModel):
    error: str = ""
    code: int = 200
    data: Any

class ScheduleBase(SQLModel):
    start_date: datetime            #시작 시간
    end_date: datetime              #종료 시간
    info: str | None = None         #일정 설명

class Schedule(ScheduleBase, table=True):
    schedule_id: UUID = Field(default_factory=uuid4, primary_key=True)

class SchedulePublic(ScheduleBase):
    schedule_id: UUID

class SchedulePost(ScheduleBase):
    schedule_id: UUID | None = None

class ScheduleList(BaseResponse):
    data: list[SchedulePublic]

class ScheduleResponse(BaseResponse):
    data: SchedulePublic