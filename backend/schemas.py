from datetime import datetime
from typing import List

from pydantic import BaseModel, EmailStr


# ---- Day 2: auth ----

class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---- Day 5: interview flow ----

class InterviewStartRequest(BaseModel):
    role: str
    company: str


class QuestionOut(BaseModel):
    id: int
    text: str
    skill_tag: str


class InterviewStartResponse(BaseModel):
    session_id: int
    question: QuestionOut


class AnswerRequest(BaseModel):
    answer_text: str


class AnswerResponse(BaseModel):
    score: float
    feedback: str
    next_question: QuestionOut


class SkillBreakdownItem(BaseModel):
    skill_tag: str
    avg_score: float
    attempts: int


class FocusArea(BaseModel):
    skill_tag: str
    avg_score: float
    recommendation: str


class ReportResponse(BaseModel):
    skill_breakdown: List[SkillBreakdownItem]
    focus_areas: List[FocusArea]