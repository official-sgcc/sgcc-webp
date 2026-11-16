from uuid import UUID
from fastapi import APIRouter
from ..internal.database import SessionDep
from ..models.group import GroupPost
from ..models.response import GroupResponse, GroupListResponse, BaseResponse
from ..internal import group as group_internal

group_router = APIRouter(prefix="/v1/group")

@group_router.get("/list", response_model=GroupListResponse)
def get_group_list(
    session: SessionDep,
    page_size: int = 20,
    page: int = 1
):
    return GroupListResponse(data=group_internal.get_group_list(session=session, page_size=page_size, page=page))

@group_router.get("/{group_id}", response_model=GroupResponse)
def get_group(
    session: SessionDep,
    group_id: UUID
):
    return GroupResponse(data=group_internal.get_group(session=session, group_id=group_id))

@group_router.post("/", response_model=GroupResponse)
def create_group(
    session: SessionDep,
    group: GroupPost
):
    return GroupResponse(data=group_internal.create_group(session=session, group=group))

@group_router.post("/{group_id}", response_model=GroupResponse)
def update_group(
    session: SessionDep,
    group_id: UUID,
    group: GroupPost
):
    return GroupResponse(data=group_internal.update_group(session=session, group_id=group_id, group=group))

@group_router.delete("/{group_id}", response_model=BaseResponse)
def delete_group(
    session: SessionDep,
    group_id: UUID
):
    group_internal.delete_group(session=session, group_id=group_id)
    
    return BaseResponse(data="")