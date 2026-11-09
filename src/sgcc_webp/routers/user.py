from uuid import UUID
from fastapi import APIRouter, HTTPException, Query
from sqlmodel import select, or_, col
from ..internal.database import SessionDep
from ..models.user import User, UserStatus, UserPost
from ..models.group import Group
from ..models.user_group_link import UserGroupLink
from ..models.response import UserResponse, UserListResponse, UserDetail, BaseResponse

user_router = APIRouter(prefix="/v1/user")

#테스트용 임시 유처 추가
@user_router.post("/", response_model=UserResponse)
def create_group(
    session: SessionDep,
    user: UserPost
):
    user_db = User.model_validate(user)

    session.add(user_db)
    session.commit()
    session.refresh(user_db)

    return UserResponse(data=UserDetail.model_validate(user_db))

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

    return UserListResponse(data=[UserDetail.model_validate(user) for user in users])

@user_router.get("/{user_id}", response_model=UserResponse)
def get_user(
    session: SessionDep,
    user_id: UUID
):
    user = session.get(User, user_id)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(data=UserDetail.model_validate(user))

@user_router.post("/{user_id}", response_model=UserResponse)
def post_user(
    session: SessionDep,
    user_id: UUID,
    user: UserPost
):
    user_db = session.get(User, user_id)

    if user_db is None:
        raise HTTPException(status_code=404, detail="User not found")

    update_user = user.model_dump(exclude_unset=True)

    user_db.sqlmodel_update(update_user)

    session.add(user_db)
    session.commit()
    session.refresh(user_db)

    return UserResponse(data=UserDetail.model_validate(user_db))

@user_router.delete("/{user_id}", response_model=BaseResponse)
def delete_user(
    session: SessionDep,
    user_id: UUID
):
    user = session.get(User, user_id)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    session.delete(user)
    session.commit()

    return BaseResponse(data="")