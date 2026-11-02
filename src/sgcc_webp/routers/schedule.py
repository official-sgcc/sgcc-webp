from uuid import UUID
from fastapi import APIRouter, HTTPException
from sqlmodel import select
from ..internal.database import SessionDep
from ..models.schedule import Schedule, SchedulePublic, ScheduleList, ScheduleResponse, SchedulePost, BaseResponse
from ..models.group import Group

schedule_router = APIRouter(prefix="/v1/group/{group_id}/schedule")

@schedule_router.get("/", response_model=ScheduleList)       #group_id의 모든 일정 get
def get_schedule(
    session: SessionDep,
    group_id: UUID,
    page_size: int = 20,
    page: int = 1
):
    group = session.get(Group, group_id)

    if group is None:
        raise HTTPException(status_code=404, detail="group not found")

    schedules = group.schedules

    start = (page - 1) * page_size
    end = page * page_size
    schedules = schedules[start:end]
    
    return ScheduleList(data=[SchedulePublic.model_validate(schedule) for schedule in schedules])

@schedule_router.post("/", response_model=ScheduleResponse)
def create_schedule(
    session: SessionDep,
    group_id: UUID,
    schedule: SchedulePost
):
    group = session.get(Group, group_id)

    if group is None:
            raise HTTPException(status_code=404, detail="group not found")

    schedule.group_id = group.id

    new_schedule = Schedule.model_validate(schedule)

    session.add(new_schedule)
    session.commit()
    session.refresh(new_schedule)

    return ScheduleResponse(data=SchedulePublic.model_validate(new_schedule))

@schedule_router.post("/{schedule_id}", response_model=ScheduleResponse)
def post_schedule(
    session: SessionDep,
    group_id: UUID,
    schedule_id: UUID,
    schedule: SchedulePost
):
    schedule_db = session.get(Schedule, schedule_id)

    if schedule_db is None:
        raise HTTPException(status_code=404, detail="schedule not found")

    if schedule_db.group_id != group_id:
         raise HTTPException(status_code=404, detail="schedule is not in group")

    update_schedule = schedule.model_dump(exclude_unset=True)

    schedule_db.sqlmodel_update(update_schedule)

    session.add(schedule_db)
    session.commit()
    session.refresh(schedule_db)

    return ScheduleResponse(data=SchedulePublic.model_validate(schedule_db))

@schedule_router.delete("/{schedule_id}", response_model=BaseResponse)
def delete_schedule(
    session: SessionDep,
    group_id: UUID,
    schedule_id: UUID
):
    schedule = session.get(Schedule, schedule_id)

    if schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found")

    session.delete(schedule)
    session.commit()

    return {
        "error": "",
        "code": 200,
        "data": ""
    }