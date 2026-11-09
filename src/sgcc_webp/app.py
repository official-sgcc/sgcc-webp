from contextlib import asynccontextmanager

from fastapi import FastAPI

from .internal.database import create_db_all

from .routers.health import health_router
from .routers.user import user_router
from .routers.group import group_router
from .routers.schedule import schedule_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_all()
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(health_router, prefix="/health")
app.include_router(user_router)
app.include_router(group_router)
app.include_router(schedule_router)
