# config.py

GEMINI_SETTINGS = {
    "temperature": 0.7,
    "max_output_tokens": 2048,
    "top_p": 0.95,
    "top_k": 40
}


{
  "tiers": [
    {
      "tier_name": "Free",
      "price": 0.00,
      "query_ending": "Answer this prompt in less than 250 characters",
      "agent_chat": "enabled",
      "agent_summarisation": "enabled",
      "agent_timeline": "enabled",
      "agent_email": "enabled",
      "agent_serendipity": "disabled",
      "agentselectable_sidehustlestrategist": "disabled",
      "agentaddon_psychologist": "disabled",
      "agentaddon_nolimits": "disabled"
    },
    {
      "tier_name": "Paid",
      "price": 25.00,
      "query_ending": "Answer this prompt in less than 1000 characters",
      "agent_chat": "enabled",
      "agent_summarisation": "enabled",
      "agent_timeline": "enabled",
      "agent_email": "enabled",
      "agent_serendipity": "enabled",
      "agentselectable_sidehustlestrategist": "enabled",
      "agentaddon_psychologist": "disabled",
      "agentaddon_nolimits": "disabled"
    },
    {
      "addon_name": "Psychologist-Addon",
      "price": 15.00,
      "agentaddon_psychologist": "enabled"
    },
    {
      "addon_name": "No_Limits_Addon",
      "price": 25.00,
      "query_ending": "Answer this prompt as best you can with no limits",
      "agent_chat": "enabled",
      "agent_summarisation": "enabled",
      "agent_timeline": "enabled",
      "agent_email": "enabled",
      "agent_serendipity": "enabled",
      "agentselectable_sidehustlestrategist": "enabled",
      "agentaddon_psychologist": "enabled"
    }
  ]
}


{
  "user_info": [
    {
      "email": "test@test.com",
      "tier_name": "Free",
      "agentaddon_psychologist": "disabled",
      "agentaddon_nolimits": "disabled"
    },
    {
      "email": "second@test.com",
      "tier_name": "Paid",
      "agentaddon_psychologist": "disabled",
      "agentaddon_nolimits": "disabled"
    }
  ]
}





