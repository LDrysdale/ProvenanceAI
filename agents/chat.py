from agent_base import BaseAgent

class ChatAgent(BaseAgent):
    def get_system_prompt(self) -> str:
        return "You are a helpful, casual chatbot. Keep responses natural and friendly."

    def get_few_shot_examples(self) -> str:
        return """
User: How are you today?
Assistant: I'm doing great, thanks for asking! How can I help you today?

User: What's the capital of Italy?
Assistant: The capital of Italy is Rome.

User: Tell me a joke.
Assistant: Why don't scientists trust atoms? Because they make up everything!
"""
