from pydantic import Field, BaseModel
from typing import Any

from .user import UserPublic
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