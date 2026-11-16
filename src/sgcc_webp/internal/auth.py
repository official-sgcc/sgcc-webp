from pwdlib import PasswordHash
from sqlmodel import select
from fastapi import HTTPException
from .database import SessionDep
from ..models.user import User, UserAccount
from ..models.response import UserSignUp, UserDetail

password_hash = PasswordHash.recommended()

def get_password_hash(password: str) -> str:
    return password_hash.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)

def user_sign_up(
    session: SessionDep,
    user_data: UserSignUp
):
    db_user_id = session.exec(select(User.id).where(User.student_id == user_data.student_id)).first

    if db_user_id is not None:
        raise HTTPException(status_code=409, detail="Student ID already exists")
    
    user = User.model_validate(user_data)

    session.add(user)
    session.flush()

    hashed_password = get_password_hash(user_data.password)

    user_account = UserAccount(user_id=user.id, student_id=user.student_id, hashed_password=hashed_password)

    session.add(user_account)
    session.commit()
    session.refresh(user)

    return UserDetail.model_validate(user)

