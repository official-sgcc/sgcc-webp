from pwdlib import PasswordHash
from sqlmodel import select
from typing import Annotated
from fastapi import HTTPException, Depends
from .database import SessionDep, get_session
from ..models.user import User, UserAccount, UserRole
from ..models.response import UserSignUp, UserDetail
from datetime import UTC, datetime, timedelta
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
import jwt
from jwt.exceptions import InvalidTokenError
from ..models.auth import Token

SECRET_KEY = "c3fb7f04c8f179ffb52e36e4626285245daaad679ebc2e659f8ef81b37975d2f"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/login/")

def get_password_hash(password: str) -> str:
    return password_hash.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)

def user_sign_up(
    session: SessionDep,
    user_data: UserSignUp
):
    db_user_id = session.exec(select(User.id).where(User.student_id == user_data.student_id)).first()

    if db_user_id is not None:
        raise HTTPException(status_code=409, detail="Student ID already exists")
    
    user = User.model_validate(user_data)
    session.add(user)
    session.flush()

    hashed_password = get_password_hash(user_data.password)

    user_account = UserAccount(user_id=user.id, username=user_data.username, hashed_password=hashed_password)

    session.add(user_account)
    session.commit()
    session.refresh(user)

    return UserDetail.model_validate(user)

DUMMY_HASH = get_password_hash("Dummy Password")

def authenticate_user(
    session: SessionDep,
    username: str,
    password: str
) -> User | None:
    user_account = session.exec(select(UserAccount).where(UserAccount.username == username)).first()

    if user_account is None:
        verify_password(password, DUMMY_HASH)
        return None

    if not verify_password(password, user_account.hashed_password):
        return None

    user = session.get(User, user_account.user_id)

    if user is None:
        return None

    return user

def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None
):
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

#로그인 시 토큰 생성
def login_for_access_token(
    session: SessionDep,
    form_data: OAuth2PasswordRequestForm
) -> Token:
    user = authenticate_user(session=session, username=form_data.username, password=form_data.password)

    if user is None:
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.student_id}, expires_delta=access_token_expires)

    return Token(access_token=access_token, token_type="bearer")
    
def verify_token(
    token: Annotated[str, Depends(oauth2_scheme)]
) -> str | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        username = payload.get("sub")
        if username is None:
            return None
    except InvalidTokenError:
        return None
    
    return username

def get_current_user(
    session: SessionDep,
    student_id: Annotated[str | None, Depends(verify_token)]
) -> User:
    if student_id is None:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user = session.exec(select(User).where(User.student_id == student_id)).first()

    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")

    return user

UserDep = Annotated[User, Depends(get_current_user)]