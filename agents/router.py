from agents.chat import ChatAgent
from agents.email import EmailAgent
from agents.summarization import SummarizationAgent
from agents.timeline import TimelineAgent
from agents.imagemergeragent import handle as imagemerge_handle

def route_to_agent(category, message, pipeline, context="", image_paths=None):
    if category == "email":
        agent = EmailAgent(pipeline, context)
        return agent.handle(message)
    elif category == "summarization":
        agent = SummarizationAgent(pipeline, context)
        return agent.handle(message)
    elif category == "timeline":
        agent = TimelineAgent(pipeline, context)
        return agent.handle(message)
    elif category == "chat":
        agent = ChatAgent(pipeline, context)
        return agent.handle(message)
    elif category == "imagemergeagent":
        return imagemerge_handle(message, context, image_paths=image_paths or [])
    else:
        return f"Sorry, I don't have an agent for the category '{category}'."

