import pytest
from agents.chat import ChatAgent

class DummyPipeline:
    def __call__(self, *args, **kwargs):
        return "dummy response"

def test_chat_agent_response():
    pipeline = DummyPipeline()
    agent = ChatAgent(pipeline, context="Hello context")
    response = agent.handle("What is this?")
    assert isinstance(response, str)
    assert "dummy" in response
