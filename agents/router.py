from agents.email import handle as email_handle
from agents.summarization import handle as summarization_handle
from agents.timeline import handle as timeline_handle
from agents.chat import handle as chat_handle
from agents.imagemergeragent import handle as imagemerge_handle  # NEW

def route_to_agent(category, message, pipeline, context=""):
    if category == "email":
        return email_handle(message, context)
    elif category == "summarization":
        return summarization_handle(message, context)
    elif category == "timeline":
        return timeline_handle(message, context)
    elif category == "chat":
        return chat_handle(message, context)
    elif category == "imagemergeagent":  # NEW CATEGORY
        return imagemerge_handle(message, context)
    else:
        return f"Sorry, I don't have an agent for the category '{category}'."

