import pytest
from agents.summarization import SummarizationAgent

class DummyPipeline:
    def __call__(self, *args, **kwargs):
        return "This is a summary."

def test_summarization_agent_response():
    pipeline = DummyPipeline()
    agent = SummarizationAgent(pipeline, context="news")
    response = agent.handle("Summarize this article about AI.")
    assert isinstance(response, str)
    assert "summary" in response.lower()
