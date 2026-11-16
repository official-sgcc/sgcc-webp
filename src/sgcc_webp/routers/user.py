from uuid import UUID
from fastapi import APIRouter
from ..internal.database import SessionDep
from ..models.user import UserStatus, UserPost
from ..models.response import UserResponse, UserListResponse, BaseResponse, UserSignUp
from ..internal import user as user_internal

user_router = APIRouter(prefix="/v1/user")

@user_router.get("/list", response_model=UserListResponse)
def get_user_list(
    session: SessionDep,
    keyword: str | None = None,         #검색어
    grade: int | None = None,           #학년
    status: UserStatus | None = None,   #학적
    role: str | None = None,            #직책
    group: UUID | None = None,          #활동 id
    page_size: int = 20,
    page: int = 1
):
    return UserListResponse(data=user_internal.get_user_list(session=session, keyword=keyword, grade=grade, status=status, role=role, group=group, page_size=page_size, page=page))

@user_router.get("/{user_id}", response_model=UserResponse)
def get_user(
    session: SessionDep,
    user_id: UUID
):
    return UserResponse(data=user_internal.get_user(session=session, user_id=user_id))

@user_router.post("/{user_id}", response_model=UserResponse)
def post_user(
    session: SessionDep,
    user_id: UUID,
    user: UserPost
):
    return UserResponse(data=user_internal.post_user(session=session, user_id=user_id, user=user))

@user_router.delete("/{user_id}", response_model=BaseResponse)
def delete_user(
    session: SessionDep,
    user_id: UUID
):
    user_internal.delete_user(session=session, user_id=user_id)
    
    return BaseResponse(data="")