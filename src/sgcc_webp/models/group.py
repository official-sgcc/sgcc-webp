from pydantic import BaseModel
from sqlmodel import SQLModel, Field, Relationship
from typing import Any, TYPE_CHECKING
from uuid import UUID, uuid4
from enum import Enum
from .user_group_link import UserGroupLink

if TYPE_CHECKING:
    from .user import User

class BaseResponse(BaseModel):
    error: str = ""
    code: int = 200
    data: Any

class GroupType(Enum):
    CLUB = "소모임"
    PROJECT = "프로젝트"

class GroupBase(SQLModel):
    name: str                       #활동명
    type: GroupType                 #활동 종류
    image: str | None = None        #사진 url
    info: str | None = None         #활동 설명
    manager: UUID | None = None     #담당자 유저 id
             #유저 id

class Group(GroupBase, table=True):
    group_id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_ids: list["User"] = Relationship(back_populates="group_ids", link_model=UserGroupLink)

class GroupPublic(GroupBase):
    group_id: UUID
    user_ids: list["User"]

class GroupPost(GroupBase):
    group_id: UUID | None = None

class GroupList(BaseResponse):
    data: list[GroupPublic]

class GroupResponse(BaseResponse):
    data: GroupPublic