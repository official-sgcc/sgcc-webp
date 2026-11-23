from sqlmodel import SQLModel, Field, Relationship
from typing import TYPE_CHECKING
from uuid import UUID, uuid4
from enum import Enum
from .user_group_link import UserGroupLink


if TYPE_CHECKING:
    from .group import Group

class UserStatus(Enum):
    ENROLLED = "재학"
    LEAVE = "휴학"
    GRADUATE = "졸업"

class UserRole(Enum):
    ADMIN = "관리자"
    MEMBER = "회원"

class UserBase(SQLModel):
    name: str
    student_id: str = Field(unique=True)
    email: str
    grade: int | None = Field(default=None)
    role: UserRole | None = Field(index=True, default=UserRole.MEMBER)
    phone: str | None = Field(default=None)
    status: UserStatus | None = Field(index=True)
    image: str | None = Field(default=None)

class User(UserBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    groups: list["Group"] = Relationship(back_populates="users", link_model=UserGroupLink)

class UserPublic(UserBase):
    id: UUID

class UserPost(UserBase):
    pass

class UserAccount(SQLModel, table=True):
    user_id: UUID = Field(primary_key=True, foreign_key="user.id")
    username: str = Field(index=True, unique=True)
    hashed_password: str
    