from graph import compiled_question_graph, compiled_eval_graph, init_skill_scores

ROLE = "Software Engineer"
COMPANY = "Goldman Sachs"

# A few sample answers fed in automatically - deliberately a mix of strong
# and weak, so you can watch the adaptive targeting actually react to them.
SAMPLE_ANSWERS = [
    "I would use a hash map to track which characters I've already seen, then loop through once. That's O(n) time and O(n) space.",
    "Um, I don't really have a good example for that, I guess I just worked hard on stuff?",
    "I'd clarify the read and write volume first, then probably use a queue-based system with a database, so it can scale horizontally later.",
]

state = {
    "role": ROLE,
    "company": COMPANY,
    "target_skill_tag": None,
    "skill_scores": init_skill_scores(),
}

for i, sample_answer in enumerate(SAMPLE_ANSWERS):
    print(f"\n{'='*60}\nQUESTION {i + 1}")

    state = {**state, **compiled_question_graph.invoke(state)}
    print("Actual skill tag for this question:", state["current_skill_tag"])
    print("Q:", state["current_question"])
    print("Rubric the AI is grading against:", state["rubric_points"])

    state["last_answer"] = sample_answer
    print("Simulated answer:", sample_answer)

    state = {**state, **compiled_eval_graph.invoke(state)}
    print(f"Score: {state['score']}/10")
    print("Feedback:", state["feedback"])
    print("Updated skill scores:", state["skill_scores"])
    print("Next question will target:", state["target_skill_tag"])