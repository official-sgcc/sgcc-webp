from uuid import UUID
from fastapi import APIRouter
from ..internal.database import SessionDep
from ..models.user import UserStatus, UserPost, UserAccount
from ..models.response import UserResponse, UserListResponse, BaseResponse, UserSignUp
from ..internal import user as user_internal

test_router = APIRouter(prefix="/v1/user")

@test_router.delete("/", response_model=BaseResponse)
def udel(
    session: SessionDep,
    user_id: UUID
):
    user = session.get(UserAccount, user_id)

    if user is None:
        return BaseResponse(data = "")

    session.delete(user)
    session.commit()

    return BaseResponse(data = "")