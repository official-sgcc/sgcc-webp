from uuid import UUID
from fastapi import APIRouter, HTTPException
from sqlmodel import select
from ..internal.database import Session
from ..models.group import Group, GroupPost
from ..models.user import User
from ..models.schedule import Schedule
from ..models.response import GroupResponse, GroupListResponse, GroupDetail, BaseResponse

def get_group_list(
    session: Session,
    page_size: int = 20,
    page: int = 1
):
    group_db = select(Group)
    
    groups = list(session.exec(group_db).all())

    start = (page - 1) * page_size
    end = page * page_size
    groups = groups[start:end]

    return [GroupDetail.model_validate(group) for group in groups]

def get_group(
    session: Session,
    group_id: UUID
):
    group = session.get(Group, group_id)

    if group is None:
        raise HTTPException(status_code=404, detail="group not found")

    return GroupDetail.model_validate(group)

def create_group(
    session: Session,
    group: GroupPost
):
    group_db = Group.model_validate(group)

    session.add(group_db)
    session.commit()
    session.refresh(group_db)

    return GroupDetail.model_validate(group_db)

def update_group(
    session: Session,
    group_id: UUID,
    group: GroupPost
):
    group_db = session.get(Group, group_id)

    if group_db is None:
        raise HTTPException(status_code=404, detail="group not found")

    update_group = group.model_dump(exclude_unset=True)

    group_db.sqlmodel_update(update_group)

    session.add(group_db)
    session.commit()
    session.refresh(group_db)

    return GroupDetail.model_validate(group_db)

def delete_group(
    session: Session,
    group_id: UUID
):
    group = session.get(Group, group_id)

    if group is None:
        raise HTTPException(status_code=404, detail="group not found")

    schedules = group.schedules

    for schedule in schedules:
        session.delete(schedule)

    session.delete(group)
    session.commit()

    return

def add_user_to_group(
    session: Session,
    group_id: UUID,
    user_id: UUID,
    current_user: User
):
    if current_user.role != "관리자":
        raise HTTPException(status_code=403, detail="Access Denied")
    
    group = session.get(Group, group_id)

    if group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    
    user = session.get(User, user_id)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if user in group.users:
        raise HTTPException(status_code=409, detail="User already in group")

    group.users.append(user)
    session.commit()
    session.refresh(group)

    return GroupDetail.model_validate(group)

def delete_user_from_group(
    session: Session,
    group_id: UUID,
    user_id: UUID,
    current_user: User
):
    if current_user.role != "관리자":
        raise HTTPException(status_code=403, detail="Access Denied")
    
    group = session.get(Group, group_id)

    if group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    
    user = session.get(User, user_id)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if user not in group.users:
        raise HTTPException(status_code=409, detail="User not in group")

    group.users.remove(user)
    session.commit()

    return