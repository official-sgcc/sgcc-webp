from uuid import UUID
from fastapi import APIRouter
from ..internal.database import SessionDep
from ..models.schedule import SchedulePost
from ..models.response import ScheduleResponse, ScheduleListResponse, BaseResponse
from ..internal import schedule as schedule_internal

schedule_router = APIRouter(prefix="/v1/group/{group_id}/schedule")

@schedule_router.get("/", response_model=ScheduleListResponse)       #group_id의 모든 일정 get
def get_schedule(
    session: SessionDep,
    group_id: UUID,
    page_size: int = 20,
    page: int = 1
):
    return ScheduleListResponse(data=schedule_internal.get_schedule(session=session, group_id=group_id, page_size=page_size, page=page))

@schedule_router.post("/", response_model=ScheduleResponse)
def create_schedule(
    session: SessionDep,
    group_id: UUID,
    schedule: SchedulePost
):
    return ScheduleResponse(data=schedule_internal.create_schedule(session=session, group_id=group_id, schedule=schedule))

@schedule_router.post("/{schedule_id}", response_model=ScheduleResponse)
def post_schedule(
    session: SessionDep,
    group_id: UUID,
    schedule_id: UUID,
    schedule: SchedulePost
):
    return ScheduleResponse(data=schedule_internal.post_schedule(session=session, group_id=group_id, schedule_id=schedule_id, schedule=schedule))

@schedule_router.delete("/{schedule_id}", response_model=BaseResponse)
def delete_schedule(
    session: SessionDep,
    group_id: UUID,
    schedule_id: UUID
):
    schedule_internal.delete_schedule(session=session, schedule_id=schedule_id, group_id=group_id)
    
    return BaseResponse(data="")