from fastapi import APIRouter
from ..internal.database import SessionDep
from ..models.response import UserResponse, UserSignUp
from ..internal import auth as auth_internal

signup_router = APIRouter(prefix="/v1/signup")

@signup_router.post("/signup", response_model=UserResponse)
def user_sign_up(
    session: SessionDep,
    user_data: UserSignUp
):
    return UserResponse(data=auth_internal.user_sign_up(session=session, user_data=user_data))
