from pydantic import BaseModel
from sqlmodel import SQLModel, Field
from typing import Any
from uuid import UUID, uuid4
from enum import Enum

class BaseResponse(BaseModel):
    error: str = ""
    code: int = 200
    data: Any

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
    group_id: list[UUID] = []                           #소모임 id

class User(UserBase, table=True):
    user_id: UUID = Field(default_factory=uuid4, primary_key=True)

class UserPublic(UserBase):
    user_id: UUID

class UserPost(UserBase):
    user_id: UUID | None = None

class UserList(BaseResponse):
    data: list[UserPublic]

class UserResponse(BaseResponse):
    data: UserPublic