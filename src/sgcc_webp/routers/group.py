from uuid import UUID
from fastapi import APIRouter, HTTPException
from sqlmodel import select
from ..internal.database import SessionDep
from ..models.group import Group, GroupPublic, GroupList, GroupResponse, GroupPost, BaseResponse

router = APIRouter(prefix="/v1/group")

@router.get("/list", response_model=GroupList)
def get_group_list(
    session: SessionDep,
    page_size: int = 20,
    page: int = 1
):
    group_db = select(Group)
    
    groups = list(session.exec(group_db).all())

    start = (page - 1) * page_size
    end = page * page_size
    groups = groups[start:end]

    return GroupList(data=[GroupPublic.model_validate(group) for group in groups])

@router.get("/{group_id}", response_model=GroupResponse)
def get_group(
    session: SessionDep,
    group_id: UUID
):
    group = session.get(Group, group_id)

    if group is None:
        raise HTTPException(status_code=404, detail="group not found")

    return GroupResponse(data=GroupPublic.model_validate(group))

@router.post("/", response_model=GroupResponse)
def create_group(
    session: SessionDep,
    group: GroupPost
):
    group_db = Group.model_validate(group)

    session.add(group_db)
    session.commit()
    session.refresh(group_db)

    return GroupResponse(data=GroupPublic.model_validate(group_db))

@router.post("/{group_id}", response_model=GroupResponse)
def update_group(
    session: SessionDep,
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

    return GroupResponse(data=GroupPublic.model_validate(group_db))

@router.delete("/{group_id}", response_model=BaseResponse)
def delete_group(
    session: SessionDep,
    group_id: UUID
):
    group = session.get(Group, group_id)

    if group is None:
        raise HTTPException(status_code=404, detail="group not found")

    session.delete(group)
    session.commit()

    return BaseResponse(data=None)