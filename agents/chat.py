# agents/chat_agent.py
from base import Agent

class ChatAgent(Agent):
    def __init__(self, pipeline, context=None):
        super().__init__(context)
        self.pipeline = pipeline

    def handle(self, message: str, context: str = "") -> str:
        # Merge external context with internal context if needed
        full_context = self.context.get("chat_history", "") + "\n" + context

        prompt = f"{full_context}\n\nUser question: {message}\nAnswer:"
        output = self.pipeline(prompt, max_tokens=256, temperature=0.7, top_p=0.9)
        answer = output.strip()

        # Update internal chat history context
        chat_history = self.context.get("chat_history", "")
        chat_history += f"\nQ: {message}\nA: {answer}"
        self.context["chat_history"] = chat_history

        return answer
