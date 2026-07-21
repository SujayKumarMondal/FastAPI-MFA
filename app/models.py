from typing import Optional
from sqlmodel import SQLModel, Field


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True)
    email: Optional[str] = None
    hashed_password: str
    is_active: bool = True
    mfa_enabled: bool = False
    mfa_secret: Optional[str] = None
