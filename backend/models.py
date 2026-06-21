from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    sessions = relationship("InterviewSession", back_populates="user")
    skill_profiles = relationship("SkillProfile", back_populates="user")


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String, nullable=False)
    company = Column(String, nullable=False)
    status = Column(String, default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="sessions")
    questions = relationship("Question", back_populates="session")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id"), nullable=False)
    skill_tag = Column(String, nullable=False)
    text = Column(String, nullable=False)
    difficulty = Column(String, default="medium")
    # NEW (Day 5): semicolon-joined rubric points for this specific question,
    # using the exact same flatten-to-string pattern as Day 3's ChromaDB
    # metadata, so the evaluation step can grade against it later even
    # though it arrives in a completely separate HTTP request.
    rubric = Column(String, nullable=True)

    session = relationship("InterviewSession", back_populates="questions")
    answer = relationship("Answer", back_populates="question", uselist=False)


class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    answer_text = Column(String, nullable=False)
    score = Column(Float, nullable=True)
    feedback_text = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    question = relationship("Question", back_populates="answer")


class SkillProfile(Base):
    __tablename__ = "skill_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    skill_tag = Column(String, nullable=False)
    avg_score = Column(Float, default=0.0)
    attempts = Column(Integer, default=0)

    user = relationship("User", back_populates="skill_profiles")