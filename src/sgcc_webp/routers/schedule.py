from uuid import UUID
from fastapi import APIRouter, HTTPException
from ..internal.database import SessionDep
from ..models.schedule import Schedule, SchedulePublic, ScheduleList, ScheduleResponse, SchedulePost, BaseResponse
from ..models.group import Group

router = APIRouter(prefix="/v1/group/{group_id}/schedule")

@router.get("/", response_model=ScheduleList)       #group_id의 모든 일정 get
def get_schedule(
    session: SessionDep,
    group_id: UUID,
    page_size: int = 20,
    page: int = 1
):
    group = session.get(Group, group_id)
    
    if group is None:
        raise HTTPException(status_code=404, detail="group not found")

    schedules = group.schedule_id

    start = (page - 1) * page_size
    end = page * page_size
    schedules = schedules[start:end]
    
    schedules = [session.get(Schedule, schedule) for schedule in schedules]
    
    return ScheduleList(data=[SchedulePublic.model_validate(schedule) for schedule in schedules])

@router.post("/", response_model=ScheduleResponse)
def create_schedule(
    session: SessionDep,
    group_id: UUID,
    schedule: SchedulePost
):
    group = session.get(Group, group_id)

    if group is None:
            raise HTTPException(status_code=404, detail="group not found")
    
    new_schedule = Schedule.model_validate(schedule)

    session.add(new_schedule)
    session.commit()
    session.refresh(new_schedule)

    group.schedule_id.append(new_schedule.schedule_id)

    session.add(group)
    session.commit()

    return ScheduleResponse(data=SchedulePublic.model_validate(new_schedule))

@router.post("/{schedule_id}", response_model=ScheduleResponse)
def post_schedule(
    session: SessionDep,
    group_id: UUID,
    schedule_id: UUID,
    schedule: SchedulePost
):
    group = session.get(Group, group_id)
    
    if group is None:
            raise HTTPException(status_code=404, detail="group not found")
    
    schedule_db = session.get(Schedule, schedule_id)

    if schedule_db is None:
        raise HTTPException(status_code=404, detail="Schedule not found")

    update_schedule = schedule.model_dump(exclude_unset=True)

    schedule_db.sqlmodel_update(update_schedule)

    session.add(schedule_db)
    session.commit()
    session.refresh(schedule_db)

    return ScheduleResponse(data=SchedulePublic.model_validate(schedule_db))

@router.delete("/{schedule_id}", response_model=BaseResponse)
def delete_schedule(
    session: SessionDep,
    group_id: UUID,
    schedule_id: UUID
):
    group = session.get(Group, group_id)

    if group is None:
        raise HTTPException(status_code=404, detail="group not found")

    schedule = session.get(Schedule, schedule_id)

    if schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found")

    group.schedule_id.remove(schedule_id)

    session.add(group)
    session.commit()

    session.delete(Schedule)
    session.commit()

    return BaseResponse(data=None)