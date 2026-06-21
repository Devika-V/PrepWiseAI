from sqlalchemy.orm import Session

import models
from graph import SKILL_TAGS

RECOMMENDATIONS = {
    "DSA": "Focus on practicing more DSA problems - NeetCode 150 (neetcode.io) and Striver's SDE Sheet are excellent free resources.",
    "System Design": "Review core system design patterns for free using resources like the 'System Design Primer' on GitHub.",
    "Behavioral": "Practice structuring answers with the STAR method (Situation, Task, Action, Result).",
    "Communication": "Practice explaining technical concepts out loud to a non-technical friend, or record yourself answering and review for clarity and conciseness.",
}


def get_skill_scores(db: Session, user_id: int) -> dict:
    """
    Loads this user's current SkillProfile rows into a simple
    {skill_tag: avg_score} dict, defaulting any skill they haven't
    attempted yet to a neutral 5.0 - mirrors graph.init_skill_scores(),
    but backed by the real database instead of an in-memory dict.
    """
    scores = {tag: 5.0 for tag in SKILL_TAGS}
    profiles = db.query(models.SkillProfile).filter(models.SkillProfile.user_id == user_id).all()
    for p in profiles:
        scores[p.skill_tag] = p.avg_score
    return scores


def has_any_history(db: Session, user_id: int) -> bool:
    return db.query(models.SkillProfile).filter(models.SkillProfile.user_id == user_id).count() > 0


def record_answer_score(db: Session, user_id: int, skill_tag: str, score: float) -> None:
    """
    Updates (or creates) this user's SkillProfile row for one skill tag,
    using a true cumulative average across every attempt they've EVER made -
    not just within the current session. This is what makes the skill-gap
    report meaningful across multiple practice sessions over time, not just
    a single sitting.
    """
    profile = (
        db.query(models.SkillProfile)
        .filter(models.SkillProfile.user_id == user_id, models.SkillProfile.skill_tag == skill_tag)
        .first()
    )
    if profile is None:
        profile = models.SkillProfile(user_id=user_id, skill_tag=skill_tag, avg_score=score, attempts=1)
        db.add(profile)
    else:
        profile.avg_score = round((profile.avg_score * profile.attempts + score) / (profile.attempts + 1), 2)
        profile.attempts += 1
    db.commit()


def build_report(db: Session, user_id: int) -> dict:
    profiles = db.query(models.SkillProfile).filter(models.SkillProfile.user_id == user_id).all()

    breakdown = [
        {"skill_tag": p.skill_tag, "avg_score": p.avg_score, "attempts": p.attempts}
        for p in profiles
    ]

    attempted = [p for p in profiles if p.attempts > 0]
    attempted.sort(key=lambda p: p.avg_score)  # weakest first

    focus_areas = [
        {
            "skill_tag": p.skill_tag,
            "avg_score": p.avg_score,
            "recommendation": RECOMMENDATIONS.get(p.skill_tag, "Keep practicing this area."),
        }
        for p in attempted[:2]
    ]

    return {"skill_breakdown": breakdown, "focus_areas": focus_areas}