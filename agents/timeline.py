from agent_base import BaseAgent

class TimelineAgent(BaseAgent):
    def get_system_prompt(self) -> str:
        return "You are a historian constructing chronological timelines for historical or project-related topics."

    def get_few_shot_examples(self) -> str:
        return """
User: The life of Albert Einstein
Assistant:
- 1879: Born in Ulm, Germany
- 1905: Publishes theory of special relativity
- 1921: Wins Nobel Prize in Physics
- 1955: Dies in Princeton, USA

User: The history of the iPhone
Assistant:
- 2007: First iPhone released
- 2010: iPhone 4 introduced FaceTime
- 2016: iPhone 7 removes headphone jack
- 2020: iPhone 12 supports 5G networks
"""
