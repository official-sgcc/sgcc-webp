from pydantic import BaseModel
from typing import Any, Optional

from .user import UserPublic, UserStatus
from .group import GroupPublic
from .schedule import SchedulePublic

class BaseResponse(BaseModel):
    error: str = ""
    code: int = 200
    data: Any

class UserDetail(UserPublic):
    groups: list[GroupPublic] = []

class UserResponse(BaseResponse):
    data: UserDetail

class UserListResponse(BaseResponse):
    data: list[UserDetail]

class GroupDetail(GroupPublic):
    users: list[UserPublic] = []
    schedules: list[SchedulePublic] = []

class GroupResponse(BaseResponse):
    data: GroupDetail

class GroupListResponse(BaseResponse):
    data: list[GroupDetail]

class ScheduleListResponse(BaseResponse):
    data: list[SchedulePublic]

class ScheduleResponse(BaseResponse):
    data: SchedulePublic

class UserSignUp(BaseModel):
    name: str
    student_id: str
    username: str
    email: str
    grade: Optional[int] = None
    phone: Optional[str] = None
    status: Optional[UserStatus] = None
    role: Optional[str] = None
    image: Optional[str] = None
    password: str

class UserLogin(BaseModel):
    username: str       #학번
    password: str       #비밀번호