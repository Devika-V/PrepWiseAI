from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

import auth
import interview_logic
import models
import schemas
from database import Base, engine, get_db
from graph import compiled_eval_graph, compiled_question_graph

Base.metadata.create_all(bind=engine)

app = FastAPI(title="PrepWise AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Day 2: auth (unchanged)
# ---------------------------------------------------------------------------

@app.post("/register", response_model=schemas.UserOut)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = models.User(
        email=user.email,
        hashed_password=auth.hash_password(user.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    token = auth.create_access_token(data={"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}


@app.get("/me", response_model=schemas.UserOut)
def read_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user


# ---------------------------------------------------------------------------
# Day 5/6: interview flow (now role-scoped for skill tracking)
# ---------------------------------------------------------------------------

def _save_question(db: Session, session_id: int, question_text: str, skill_tag: str, rubric_points: list) -> models.Question:
    question = models.Question(
        session_id=session_id,
        skill_tag=skill_tag,
        text=question_text,
        rubric="; ".join(rubric_points),
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


def _get_pending_question(db: Session, session: models.InterviewSession) -> models.Question:
    question = (
        db.query(models.Question)
        .filter(models.Question.session_id == session.id)
        .order_by(models.Question.id.desc())
        .first()
    )
    if question is None or question.answer is not None:
        raise HTTPException(status_code=400, detail="No pending question for this session - start a new interview.")
    return question


@app.post("/interview/start", response_model=schemas.InterviewStartResponse)
def start_interview(
    body: schemas.InterviewStartRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    session = models.InterviewSession(user_id=current_user.id, role=body.role, company=body.company)
    db.add(session)
    db.commit()
    db.refresh(session)

    # A returning user with prior history IN THIS ROLE starts already
    # targeting their current weakest skill for that role. A brand-new
    # user, or one who's never practiced this particular role before,
    # gets a no-preference "spread" first question.
    target_skill_tag = None
    if interview_logic.has_any_history(db, current_user.id, body.role):
        scores = interview_logic.get_skill_scores(db, current_user.id, body.role)
        target_skill_tag = min(scores, key=scores.get)

    state = {"role": body.role, "company": body.company, "target_skill_tag": target_skill_tag}
    result = compiled_question_graph.invoke(state)

    if not result.get("current_question"):
        raise HTTPException(
            status_code=400,
            detail="No questions found for that role/company combination - check it matches your seeded data exactly.",
        )

    question = _save_question(
        db, session.id, result["current_question"], result["current_skill_tag"], result["rubric_points"]
    )

    return {
        "session_id": session.id,
        "question": {"id": question.id, "text": question.text, "skill_tag": question.skill_tag},
    }


@app.post("/interview/{session_id}/answer", response_model=schemas.AnswerResponse)
def submit_answer(
    session_id: int,
    body: schemas.AnswerRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    session = db.query(models.InterviewSession).filter(models.InterviewSession.id == session_id).first()
    if session is None or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Interview session not found")

    pending_question = _get_pending_question(db, session)

    eval_state = {
        "role": session.role,
        "company": session.company,
        "current_skill_tag": pending_question.skill_tag,
        "current_question": pending_question.text,
        "rubric_points": (pending_question.rubric or "").split("; "),
        "last_answer": body.answer_text,
        "skill_scores": interview_logic.get_skill_scores(db, current_user.id, session.role),
    }
    eval_result = compiled_eval_graph.invoke(eval_state)

    answer = models.Answer(
        question_id=pending_question.id,
        answer_text=body.answer_text,
        score=eval_result["score"],
        feedback_text=eval_result["feedback"],
    )
    db.add(answer)
    db.commit()

    interview_logic.record_answer_score(db, current_user.id, pending_question.skill_tag, eval_result["score"])

    next_state = {
        "role": session.role,
        "company": session.company,
        "target_skill_tag": eval_result["target_skill_tag"],
    }
    next_result = compiled_question_graph.invoke(next_state)
    next_question = _save_question(
        db, session.id, next_result["current_question"], next_result["current_skill_tag"], next_result["rubric_points"]
    )

    return {
        "score": eval_result["score"],
        "feedback": eval_result["feedback"],
        "next_question": {"id": next_question.id, "text": next_question.text, "skill_tag": next_question.skill_tag},
    }


@app.get("/interview/{session_id}/report", response_model=schemas.ReportResponse)
def get_report(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    session = db.query(models.InterviewSession).filter(models.InterviewSession.id == session_id).first()
    if session is None or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Interview session not found")

    return interview_logic.build_report(db, current_user.id, session.role)