from uuid import UUID
from sqlmodel import select, or_, col
from .database import SessionDep
from .auth import get_current_user
from ..models.user import User, UserStatus, UserPost, UserAccount, UserRole
from ..models.group import Group
from ..models.user_group_link import UserGroupLink
from ..models.response import UserDetail, UserSignUp
from fastapi import HTTPException, Depends
from typing import Annotated

def get_user_list(
    session: SessionDep,
    current_user: User,
    keyword: str | None = None,         #검색어
    grade: int | None = None,           #학년
    status: UserStatus | None = None,   #학적
    role: UserRole | None = None,            #직책
    group: UUID | None = None,          #활동 id
    page_size: int = 20,
    page: int = 1
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Access Denied")
    
    user_db = select(User)

    if keyword:
        user_db = user_db.where(
            or_(
                col(User.name).contains(keyword),
                col(User.student_id).contains(keyword),
                col(User.phone).contains(keyword),
            )
        )

    if grade is not None:
        user_db = user_db.where(User.grade == grade)

    if status is not None:
        user_db = user_db.where(User.status == status)

    if role is not None:
        user_db = user_db.where(User.role == role)

    if group is not None:
        user_db = user_db.join(UserGroupLink).join(Group).where(Group.id == group)

    users = list(session.exec(user_db).all())

    start = (page - 1) * page_size
    end = page * page_size
    users = users[start:end]

    return [UserDetail.model_validate(user) for user in users]

def get_user(
    session: SessionDep,
    user_id: UUID,
    current_user: User
):
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access Denied")
    
    user = session.get(User, user_id)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return UserDetail.model_validate(user)

def post_user(
    session: SessionDep,
    user_id: UUID,
    user: UserPost,
    current_user: User
):
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access Denied")
    
    user_db = session.get(User, user_id)

    if user_db is None:
        raise HTTPException(status_code=404, detail="User not found")

    update_user = user.model_dump(exclude_unset=True)

    user_db.sqlmodel_update(update_user)

    session.add(user_db)
    session.commit()
    session.refresh(user_db)

    return UserDetail.model_validate(user_db)

def delete_user(
    session: SessionDep,
    user_id: UUID,
    current_user: User
):
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access Denied")
    
    user = session.get(User, user_id)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    session.delete(user)
    session.commit()

    return
