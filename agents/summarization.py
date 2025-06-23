def handle(question: str, pipeline, context: str = "") -> str:
    system_prompt = "You are an expert summarizer that condenses content without losing essential meaning."
    prompt = f"{system_prompt}\n{context}\n\nInput: {question}\n\nSummary:"
    return pipeline(prompt, max_tokens=150, temperature=0.5).strip()
