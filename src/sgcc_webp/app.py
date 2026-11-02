from fastapi import FastAPI

from .routers.health import health_router
from .routers.user import user_router
from .routers.group import group_router
from .routers.schedule import schedule_router

app = FastAPI()

app.include_router(health_router, prefix="/health")
app.include_router(user_router)
app.include_router(group_router)
app.include_router(schedule_router)
