# base.py
from abc import ABC, abstractmethod

def categorize_question(message: str) -> str:
    # Your existing categorization logic
    ...

class Agent(ABC):
    def __init__(self, context=None):
        # Initialize with optional context dict (can be anything you want)
        self.context = context or {}

    @abstractmethod
    def handle(self, message: str, context: str = "") -> str:
        """
        Process the message with optional external context, 
        and possibly update internal context.
        """
        pass
