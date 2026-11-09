from pydantic import BaseModel
from sqlmodel import SQLModel, Field, Relationship
from typing import Any, TYPE_CHECKING
from uuid import UUID, uuid4
from enum import Enum
from .user_group_link import UserGroupLink


if TYPE_CHECKING:
    from .group import Group

class UserStatus(Enum):
    ENROLLED = "재학"
    LEAVE = "휴학"
    GRADUATE = "졸업"

class UserBase(SQLModel):
    name: str                                           #이름
    student_id: str                                     #학번
    grade: int                                          #학년
    phone: str                                          #전화번호
    status: UserStatus = Field(index=True)              #학적
    role: str | None = Field(index=True, default=None)  #직책
    image: str | None = Field(default=None)             #사진 url

class User(UserBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    groups: list["Group"] = Relationship(back_populates="users", link_model=UserGroupLink)        #소모임 id

class UserPublic(UserBase):
    id: UUID

class UserPost(UserBase):
    pass
