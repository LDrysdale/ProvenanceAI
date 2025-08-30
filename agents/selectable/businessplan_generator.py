from agent_base import BaseAgent

class BusinessPlanGeneratorAgent(BaseAgent):
    def get_system_prompt(self) -> str:
        return "You are a professional assistant helping users create and manage their business plans."

    def get_few_shot_examples(self) -> str:
        return """
User: Request a meeting with Dr. Smith next week
Assistant: Dear Dr. Smith, I hope this message finds you well. I would like to schedule a meeting with you sometime next week. Please let me know your availability.

User: Apologize for missing the deadline
Assistant: Dear Team, I sincerely apologize for not meeting the deadline. I understand the importance of timely submissions and will ensure it doesn't happen again.

User: Thank a client for their feedback
Assistant: Dear Client, thank you for your valuable feedback. We appreciate your time and effort in helping us improve our services.
"""
