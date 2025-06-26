import pytest
from agents.email import EmailAgent

class DummyPipeline:
    def __call__(self, *args, **kwargs):
        return "Dear user, this is your email."

def test_email_agent_response():
    pipeline = DummyPipeline()
    agent = EmailAgent(pipeline, context="Professional")
    response = agent.handle("Please draft a business email.")
    assert isinstance(response, str)
    assert "email" in response.lower()
