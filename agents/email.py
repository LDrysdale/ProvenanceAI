def handle(question: str, pipeline, context: str = "") -> str:
    system_prompt = "You are a professional assistant writing clear, respectful, and concise business emails."
    prompt = f"{system_prompt}\n{context}\n\nInstruction: {question}\n\nEmail:"
    return pipeline(prompt, max_tokens=256, temperature=0.7).strip()
