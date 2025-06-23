def handle(question: str, pipeline, context: str = "") -> str:
    system_prompt = "You are a historian constructing chronological timelines for historical or project-related topics."
    prompt = f"{system_prompt}\n{context}\n\nTopic: {question}\n\nTimeline:"
    return pipeline(prompt, max_tokens=200, temperature=0.6).strip()
