import pytest
from agents.timeline import TimelineAgent

class DummyPipeline:
    def __call__(self, *args, **kwargs):
        return "Timeline: Event A -> Event B"

def test_timeline_agent_response():
    pipeline = DummyPipeline()
    agent = TimelineAgent(pipeline, context="Historical facts")
    response = agent.handle("Give me a timeline of events.")
    assert isinstance(response, str)
    assert "Timeline" in response
