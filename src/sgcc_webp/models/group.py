from pydantic import BaseModel
from sqlmodel import SQLModel, Field, Relationship
from typing import Any, TYPE_CHECKING
from uuid import UUID, uuid4
from enum import Enum
from .user_group_link import UserGroupLink

if TYPE_CHECKING:
    from .user import User
    from .schedule import Schedule

class GroupType(Enum):
    CLUB = "소모임"
    PROJECT = "프로젝트"

class GroupBase(SQLModel):
    name: str                       #활동명
    type: GroupType                 #활동 종류
    image: str | None = None        #사진 url
    info: str | None = None         #활동 설명
    manager: UUID | None = None     #담당자 유저 id

class Group(GroupBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    users: list["User"] = Relationship(back_populates="groups", link_model=UserGroupLink)         #유저 id
    schedules: list["Schedule"] = Relationship(back_populates="group")

class GroupPublic(GroupBase):
    id: UUID

class GroupPost(GroupBase):
    pass
