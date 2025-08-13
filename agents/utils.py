def categorize_question(message: str, pipeline) -> str:
    """
    Categorizes the user's message using few-shot prompting via the provided pipeline function.
    """
    prompt = f"""You are an intelligent text classifier. Choose the correct category for the user's message.

Categories:
- email
- summarization
- timeline
- imagemergeagent
- chat

Examples:
User: Please summarize the following text about climate change.
Category: summarization

User: Can you help me compose a business email to my manager?
Category: email

User: What are the key events in the history of the Roman Empire?
Category: timeline

User: images: img1.png, img2.png
please merge image1 with image2 using a blend effect.
Category: imagemergeagent

User: Hey, what's up? How's your day?
Category: chat

User: {message.strip()}
Category:"""

    try:
        result = pipeline(prompt, max_output_tokens=1, temperature=0.0).strip().lower()
    except Exception as e:
        print(f"[ERROR] Categorization failed: {str(e)}")
        return "chat"

    valid_categories = {"email", "summarization", "timeline", "imagemergeagent", "chat"}
    return result if result in valid_categories else "chat"
