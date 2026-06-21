from typing import TypedDict, List, Optional

from langgraph.graph import StateGraph, START, END

import rag
import llm

SKILL_TAGS = ["DSA", "System Design", "Behavioral", "Communication"]


class InterviewState(TypedDict):
    role: str
    company: str
    target_skill_tag: Optional[str]    # which skill retrieval should aim for next (None = no preference yet)
    current_skill_tag: Optional[str]   # which skill the CURRENT question actually belongs to
    retrieved_context: List[dict]
    current_question: str
    rubric_points: List[str]
    last_answer: Optional[str]
    score: Optional[float]
    feedback: Optional[str]
    skill_scores: dict


def init_skill_scores() -> dict:
    # Everyone starts at a neutral 5.0 - this gives select_next_skill_node
    # something sensible to compare against before any real answers exist,
    # so the very first "weakest skill" pick isn't meaningless.
    return {tag: 5.0 for tag in SKILL_TAGS}


# ---------------------------------------------------------------------------
# Graph 1: generating the next question
# ---------------------------------------------------------------------------

def retrieve_context_node(state: InterviewState) -> dict:
    matches = rag.retrieve_questions(
        role=state["role"],
        company=state["company"],
        skill_tag=state.get("target_skill_tag"),
        top_k=3,
    )
    return {"retrieved_context": matches}


def generate_question_node(state: InterviewState) -> dict:
    candidates = state["retrieved_context"]

    if not candidates:
        # Safety net - if retrieval somehow returns nothing, never let the
        # interview hard-crash. Fall back to a generic, always-safe question.
        return {
            "current_question": "Tell me about a project you're proud of and why.",
            "rubric_points": ["gives a specific example", "explains the impact"],
            "current_skill_tag": state.get("target_skill_tag") or "Behavioral",
        }

    best = candidates[0]

    prompt = (
        f"You are a professional interviewer for a {state['role']} role at {state['company']}.\n"
        "Rephrase the question below in a natural, conversational interviewer voice. "
        "Keep the technical meaning exactly the same - do not change what is actually "
        "being asked. Return ONLY the rephrased question, nothing else.\n\n"
        f"Original question: {best['question']}"
    )

    phrased = llm.generate_text(prompt)

    return {
        "current_question": phrased or best["question"],
        "rubric_points": best["rubric_points"],
        "current_skill_tag": best["skill_tag"],
    }


question_graph = StateGraph(InterviewState)
question_graph.add_node("retrieve", retrieve_context_node)
question_graph.add_node("generate", generate_question_node)
question_graph.add_edge(START, "retrieve")
question_graph.add_edge("retrieve", "generate")
question_graph.add_edge("generate", END)
compiled_question_graph = question_graph.compile()


# ---------------------------------------------------------------------------
# Graph 2: evaluating an answer and deciding what skill to target next
# ---------------------------------------------------------------------------

def evaluate_answer_node(state: InterviewState) -> dict:
    prompt = (
        "You are grading a candidate's interview answer.\n\n"
        f"Question: {state['current_question']}\n"
        f"Candidate's answer: {state['last_answer']}\n"
        f"What a strong answer should cover: {', '.join(state['rubric_points'])}\n\n"
        "Score the answer from 0 to 10 and give two sentences of specific, "
        "constructive feedback. Respond ONLY in this exact JSON shape: "
        '{"score": <number>, "feedback": "<text>"}'
    )

    result = llm.generate_json(prompt)
    score = float(result.get("score", 5.0))
    score = max(0.0, min(10.0, score))  # keep it inside a sane 0-10 range no matter what the model says

    return {"score": score, "feedback": result.get("feedback", "")}


def update_skill_node(state: InterviewState) -> dict:
    tag = state["current_skill_tag"]
    scores = dict(state["skill_scores"])
    # A simple rolling average - nudges the stored score halfway toward the
    # newest result, rather than fully overwriting or just appending forever.
    scores[tag] = round((scores.get(tag, 5.0) + state["score"]) / 2, 2)
    return {"skill_scores": scores}


def select_next_skill_node(state: InterviewState) -> dict:
    scores = state["skill_scores"]
    weakest_tag = min(scores, key=scores.get)
    return {"target_skill_tag": weakest_tag}


eval_graph = StateGraph(InterviewState)
eval_graph.add_node("evaluate", evaluate_answer_node)
eval_graph.add_node("update_skill", update_skill_node)
eval_graph.add_node("select_next", select_next_skill_node)
eval_graph.add_edge(START, "evaluate")
eval_graph.add_edge("evaluate", "update_skill")
eval_graph.add_edge("update_skill", "select_next")
eval_graph.add_edge("select_next", END)
compiled_eval_graph = eval_graph.compile()