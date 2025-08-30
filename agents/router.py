import logging
from datetime import datetime, timezone
from firebase_admin import firestore
from agents.chat import ChatAgent
from agents.email import EmailAgent
from agents.summarization import SummarizationAgent
from agents.timeline import TimelineAgent
from agents.imagemergeragent import handle as imagemerge_handle
# Import your actual selectable agent classes
from agents.selectable.ideasgenerator import SerendipityEnginePrompt as IdeasGeneratorAgent
from agents.selectable.momentum_manager import MomentumManagerAgent
from agents.selectable.businessplan_generator import BusinessPlanGeneratorAgent
from agents.selectable.psychologist import PsychologistAgent

logger = logging.getLogger("app_logger")
db = firestore.client()

# -------------------------
# User cache
# -------------------------
USER_CACHE = {}

def get_user_data(uid: str):
    if uid in USER_CACHE:
        return USER_CACHE[uid]

    user_ref = db.collection("users").document(uid)
    doc = user_ref.get()
    if not doc.exists:
        raise ValueError(f"User {uid} not found in Firestore")

    user_data = doc.to_dict()
    now = datetime.now(timezone.utc)

    # -------------------------
    # Auto-downgrade paid users if membership expired
    # -------------------------
    membership_expiry = user_data.get("membershipExpiry")
    if membership_expiry and hasattr(membership_expiry, "to_datetime"):
        expiry_dt = membership_expiry.to_datetime().replace(tzinfo=timezone.utc)
        if user_data.get("tier") == "paid" and now > expiry_dt:
            logger.info(f"User {uid} paid membership expired. Downgrading to free tier.")
            user_data["tier"] = "free"
            user_data["subscriptionStatus"] = "expired"
            user_ref.update({
                "tier": "free",
                "subscriptionStatus": "expired"
            })

    # -------------------------
    # Check add-on expiries
    # -------------------------
    for addon in ["psychologist", "unlimited"]:
        addon_key = f"addon_{addon}"
        expiry_key = f"addon_{addon}_expiry"
        if user_data.get(addon_key) and user_data.get(expiry_key):
            expiry_dt = user_data[expiry_key]
            if hasattr(expiry_dt, "to_datetime"):
                expiry_dt = expiry_dt.to_datetime().replace(tzinfo=timezone.utc)
            if now > expiry_dt:
                logger.info(f"User {uid} {addon} addon expired.")
                user_data[addon_key] = False
                user_ref.update({addon_key: False})

    USER_CACHE[uid] = user_data
    return user_data

# -------------------------
# Selectable agent mapping and access rules
# -------------------------
SELECTABLE_AGENTS = {
    "Ideas Generator": (IdeasGeneratorAgent, lambda u: True),
    "Momentum Manager": (MomentumManagerAgent, lambda u: u.get("tier") == "paid"),
    "Business Plan Generator": (BusinessPlanGeneratorAgent, lambda u: u.get("tier") == "paid"),
    "Psychologist": (PsychologistAgent, lambda u: u.get("addon_psychologist") is True)
}

# Core agents mapping
CORE_AGENTS = {
    "email": EmailAgent,
    "summarization": SummarizationAgent,
    "timeline": TimelineAgent,
    "chat": ChatAgent
}

# -------------------------
# Character limit context
# -------------------------
def apply_character_limit_context(user_data, context):
    if user_data.get("addon_unlimited"):
        return context
    if user_data.get("tier") == "free":
        return context + " Limit the response to 250 characters."
    if user_data.get("tier") == "paid":
        return context + " Limit the response to 1000 characters."
    return context

# -------------------------
# Helper: List available selectable agents
# -------------------------
def get_available_selectable_agents(user_data):
    available = []
    for agent_name, (_, access_func) in SELECTABLE_AGENTS.items():
        if access_func(user_data):
            available.append(agent_name)
    return available

def is_agent_available(agent_name, user_data):
    access_func = SELECTABLE_AGENTS.get(agent_name, (None, lambda u: True))[1]
    return access_func(user_data)

# -------------------------
# Route prompt to agent
# -------------------------
def route_to_agent(uid, category, message, pipeline, context="", image_paths=None):
    image_paths = image_paths or []

    try:
        # Fetch user data (auto-downgrades expired paid membership and expired addons)
        user_data = get_user_data(uid)

        # Apply character limit context
        context = apply_character_limit_context(user_data, context)

        # Debug log available selectable agents
        available_agents = get_available_selectable_agents(user_data)
        logger.debug(f"User {uid} has access to selectable agents: {available_agents}")

        logger.info(f"Routing request for user {uid} with category '{category}'")

        # --------- Core Agents ---------
        if category in CORE_AGENTS:
            agent_class = CORE_AGENTS[category]
            agent = agent_class(pipeline, context)
            message_with_context = f"{agent.build_context()}{message}"
            response = agent.handle(message_with_context)
            logger.info(f"{category} agent handled the request successfully")
            return response

        # --------- Image merge agent ---------
        if category == "imagemergeagent":
            if not image_paths or len(image_paths) < 2:
                logger.warning("Insufficient images uploaded for image merging.")
                return "Please upload at least two images for merging."
            response = imagemerge_handle(message, context, image_paths=image_paths)
            logger.info("imagemerge_handle processed the request successfully")
            return response

        # --------- Selectable Agents ---------
        if category in SELECTABLE_AGENTS:
            agent_class, access_func = SELECTABLE_AGENTS[category]
            if not access_func(user_data):
                logger.warning(f"{category} agent is not enabled for this user.")
                return f"The {category} agent is not available for your current tier or add-ons."

            agent = agent_class(pipeline, context)
            message_with_context = f"{agent.build_context()}{message}"
            response = agent.handle(message_with_context)
            logger.info(f"{category} agent handled the request successfully")
            return response

        # --------- Unknown category ---------
        logger.warning(f"No agent found for category: '{category}'")
        return f"Sorry, I don't have an agent for the category '{category}'."

    except Exception as e:
        logger.error(f"Error in routing or handling: {str(e)}", exc_info=True)
        return "Sorry, something went wrong while processing your request."
