from sqlalchemy.orm import Session

import models
from graph import ROLE_SKILL_TAGS, SKILL_TAGS

RECOMMENDATIONS = {
    "DSA": "Focus on practicing more DSA problems - NeetCode 150 (neetcode.io) and Striver's SDE Sheet are excellent free resources.",
    "System Design": "Review core system design patterns for free using resources like the 'System Design Primer' on GitHub.",
    "Behavioral": "Practice structuring answers with the STAR method (Situation, Task, Action, Result).",
    "Communication": "Practice explaining technical concepts out loud to a non-technical friend, or record yourself answering and review for clarity and conciseness.",
    "SQL": "Practice writing SQL queries hands-on - free platforms like LeetCode's database section, StrataScratch, or Mode's SQL tutorial are excellent for hands-on reps.",
    "Statistics": "Review core statistics concepts (significance testing, distributions, confidence intervals) - free resources like Khan Academy's statistics course are a solid refresher.",
    "Product Sense": "Practice structuring product questions with a clear framework (user, problem, solution, metrics) - free PM interview question banks like Exponent's blog are a good start.",
    "Execution & Metrics": "Practice defining clear success metrics (a primary metric plus guardrail metrics) for any feature you discuss.",
    "Technical Finance": "Review core valuation concepts (DCF, comparable companies) and basic accounting statement linkages - free resources like Corporate Finance Institute's articles are a good start.",
    "Market Awareness": "Stay current on major market news and practice articulating your view on a recent deal or market move in under a minute.",
    "Marketing Analytics": "Practice working through campaign performance questions (CTR, conversion rate, CAC, ROAS) and how you'd diagnose an underperforming campaign.",
    "Campaign Strategy": "Practice structuring a campaign brief end-to-end: audience, channel choice, messaging, and how you'd measure success.",
}


def get_skill_scores(db: Session, user_id: int, role: str) -> dict:
    """
    Loads this user's current SkillProfile rows into a {skill_tag: avg_score}
    dict, scoped ONLY to the tags relevant to the given role - so a Software
    Engineer interview is never influenced by, say, a leftover "Market
    Awareness" score from a past Investment Banking Analyst session.
    """
    relevant_tags = ROLE_SKILL_TAGS.get(role, SKILL_TAGS)
    scores = {tag: 5.0 for tag in relevant_tags}
    profiles = (
        db.query(models.SkillProfile)
        .filter(models.SkillProfile.user_id == user_id, models.SkillProfile.skill_tag.in_(relevant_tags))
        .all()
    )
    for p in profiles:
        scores[p.skill_tag] = p.avg_score
    return scores


def has_any_history(db: Session, user_id: int, role: str) -> bool:
    relevant_tags = ROLE_SKILL_TAGS.get(role, SKILL_TAGS)
    return (
        db.query(models.SkillProfile)
        .filter(models.SkillProfile.user_id == user_id, models.SkillProfile.skill_tag.in_(relevant_tags))
        .count()
        > 0
    )


def record_answer_score(db: Session, user_id: int, skill_tag: str, score: float) -> None:
    """
    Updates (or creates) this user's SkillProfile row for one skill tag,
    using a true cumulative average across every attempt they've EVER made.
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


def build_report(db: Session, user_id: int, role: str) -> dict:
    """
    Builds a report scoped to the given role's relevant skill tags only - so
    a Data Analyst session's report never shows irrelevant rows like "DSA"
    or "Market Awareness" that don't apply to that role at all.
    """
    relevant_tags = ROLE_SKILL_TAGS.get(role, SKILL_TAGS)
    profiles = (
        db.query(models.SkillProfile)
        .filter(models.SkillProfile.user_id == user_id, models.SkillProfile.skill_tag.in_(relevant_tags))
        .all()
    )
    existing = {p.skill_tag: p for p in profiles}

    breakdown = []
    for tag in relevant_tags:
        p = existing.get(tag)
        breakdown.append(
            {
                "skill_tag": tag,
                "avg_score": p.avg_score if p else 0.0,
                "attempts": p.attempts if p else 0,
            }
        )

    attempted = [b for b in breakdown if b["attempts"] > 0]
    attempted.sort(key=lambda b: b["avg_score"])  # weakest first

    focus_areas = [
        {
            "skill_tag": b["skill_tag"],
            "avg_score": b["avg_score"],
            "recommendation": RECOMMENDATIONS.get(b["skill_tag"], "Keep practicing this area."),
        }
        for b in attempted[:2]
    ]

    return {"skill_breakdown": breakdown, "focus_areas": focus_areas}