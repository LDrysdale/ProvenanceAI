import logging
from agents.chat import ChatAgent
from agents.email import EmailAgent
from agents.summarization import SummarizationAgent
from agents.timeline import TimelineAgent
from agents.imagemergeragent import handle as imagemerge_handle

logger = logging.getLogger("app_logger")  # Use same logger name as main.py

def route_to_agent(category, message, pipeline, context="", image_paths=None):
    image_paths = image_paths or []  # Ensure list

    logger.info(f"Routing request with category '{category}' and message: {message[:50]!r}")

    try:
        if category == "email":
            logger.debug("Instantiating EmailAgent")
            agent = EmailAgent(pipeline, context)
            response = agent.handle(message)
            logger.info("EmailAgent handled the request successfully")
            return response

        elif category == "summarization":
            logger.debug("Instantiating SummarizationAgent")
            agent = SummarizationAgent(pipeline, context)
            response = agent.handle(message)
            logger.info("SummarizationAgent handled the request successfully")
            return response

        elif category == "timeline":
            logger.debug("Instantiating TimelineAgent")
            agent = TimelineAgent(pipeline, context)
            response = agent.handle(message)
            logger.info("TimelineAgent handled the request successfully")
            return response

        elif category == "chat":
            logger.debug("Instantiating ChatAgent")
            agent = ChatAgent(pipeline, context)
            response = agent.handle(message)
            logger.info("ChatAgent handled the request successfully")
            return response

        elif category == "imagemergeagent":
            if not image_paths or len(image_paths) < 2:
                logger.warning("Insufficient images uploaded for image merging.")
                return "Please upload at least two images for merging."
            logger.debug("Calling imagemerge_handle with multiple image support")
            response = imagemerge_handle(message, context, image_paths=image_paths)
            logger.info("imagemerge_handle processed the request successfully")
            return response

        else:
            logger.warning(f"No agent found for category: '{category}'")
            return f"Sorry, I don't have an agent for the category '{category}'."

    except Exception as e:
        logger.error(f"Error in routing or handling: {str(e)}", exc_info=True)  # Full traceback
        return "Sorry, something went wrong while processing your request."
