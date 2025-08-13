from config import GEMINI_SETTINGS
from gemini_model import gemini_generate  # assuming you put the function in gemini_generate.py

class BaseAgent:
    def __init__(self, pipeline=gemini_generate, context=None):
        self.pipeline = pipeline
        self.context = context or ""

    def get_system_prompt(self) -> str:
        return ""

    def get_few_shot_examples(self) -> str:
        return ""

    def handle(self, question: str) -> str:
        """
        Handles a user question by creating a full prompt and calling the Gemini API.
        Passes max_output_tokens and temperature from GEMINI_SETTINGS.
        """
        system_prompt = self.get_system_prompt()
        few_shot = self.get_few_shot_examples()
        prompt = f"{system_prompt}\n{few_shot}\nUser: {question}\nAssistant:"

        # Call gemini_generate with correct arguments
        return self.pipeline(
            prompt,
            max_output_tokens=GEMINI_SETTINGS.get("max_output_tokens", 2048),
            temperature=GEMINI_SETTINGS.get("temperature", 0.7)
        ).strip()

