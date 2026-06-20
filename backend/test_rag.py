from rag import retrieve_questions

print("=== Test 1: Goldman Sachs, Behavioral ===")
results = retrieve_questions(role="Software Engineer", company="Goldman Sachs", skill_tag="Behavioral", top_k=2)
for r in results:
    print("-" * 40)
    print("Question:", r["question"])
    print("Skill tag:", r["skill_tag"], "| Difficulty:", r["difficulty"])
    print("Rubric points:", r["rubric_points"])

print("\n=== Test 2: Google, no skill_tag filter (returns a spread) ===")
results = retrieve_questions(role="Software Engineer", company="Google", top_k=3)
for r in results:
    print("-" * 40)
    print("Question:", r["question"])
    print("Skill tag:", r["skill_tag"])