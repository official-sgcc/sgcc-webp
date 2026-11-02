from sqlmodel import SQLModel, Field
from uuid import UUID

class UserGroupLink(SQLModel, table=True):
    user_id: UUID | None = Field(default=None, foreign_key="user.user_id", primary_key=True)
    group_id: UUID | None = Field(default=None, foreign_key="group.group_id", primary_key=True)