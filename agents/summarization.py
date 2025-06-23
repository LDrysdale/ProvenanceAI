from agent_base import BaseAgent

class SummarizationAgent(BaseAgent):
    def get_system_prompt(self) -> str:
        return "You are an expert summarizer that condenses content without losing essential meaning."

    def get_few_shot_examples(self) -> str:
        return """
User: Artificial Intelligence is the simulation of human intelligence processes by machines. It includes learning, reasoning, and self-correction.
Assistant: AI mimics human intelligence and involves learning and reasoning.

User: The solar system includes the Sun and all objects orbiting it, such as planets, moons, asteroids, and comets.
Assistant: The solar system consists of the Sun and its orbiting celestial bodies.

User: The history of the internet spans several decades with major milestones including ARPANET, the introduction of the World Wide Web, and the rise of social media.
Assistant: The internet evolved over decades, starting with ARPANET, the web, and social media.
"""
