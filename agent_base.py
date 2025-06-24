class BaseAgent:
    def __init__(self, pipeline, context=None):
        self.pipeline = pipeline
        self.context = context or ""

    def get_system_prompt(self) -> str:
        # Override in subclasses
        return ""

    def get_few_shot_examples(self) -> str:
        # Override in subclasses
        return ""

    def handle(self, question: str) -> str:
        system_prompt = self.get_system_prompt()
        few_shot = self.get_few_shot_examples()
        prompt = f"{system_prompt}\n{few_shot}\nUser: {question}\nAssistant:"
        return self.pipeline(prompt, max_tokens=150, temperature=0.9).strip()
