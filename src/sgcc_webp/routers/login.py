from fastapi import APIRouter, Depends
from typing import Annotated
from ..internal.database import SessionDep
from ..internal import auth as auth_internal
from fastapi.security import OAuth2PasswordRequestForm
from ..models.auth import Token

login_router = APIRouter(prefix="/v1/login")

@login_router.post("/", response_model=Token)
async def user_sign_up(
    session: SessionDep,
    user_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    return auth_internal.login_for_access_token(session, user_data)
