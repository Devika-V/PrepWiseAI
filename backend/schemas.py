from datetime import datetime
from pydantic import BaseModel, EmailStr


# ---- These define what data is allowed IN to your API ----

class UserCreate(BaseModel):
    email: EmailStr
    password: str


# ---- This defines what data is allowed OUT of your API ----
# Notice it does NOT include hashed_password - we never want to
# accidentally send a password hash back in an API response.

class UserOut(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True  # lets this read directly from a SQLAlchemy model object


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"