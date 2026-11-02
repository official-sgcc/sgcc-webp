from typing import Annotated

from sqlmodel import create_engine, SQLModel, Session
from fastapi import Depends

db_file = "database.db"
db_url = f"sqlite:///{db_file}"

connect_arg = {"check_same_thread": False}
engine = create_engine(db_url, connect_args=connect_arg)

def create_db_all():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]