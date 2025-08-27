import asyncio
import os
from dotenv import load_dotenv
from chat_history import get_chat_history

# Load environment variables from .env file
load_dotenv()

async def print_history(user_id: str, limit: int = 50):
    history = await get_chat_history(user_id, limit)
    if not history:
        print(f"No chat history found for user_id: {user_id}")
    else:
        print(f"Chat history for user_id: {user_id} (showing up to {limit} entries):")
        for entry in history:
            print(entry)

if __name__ == "__main__":
    # Replace this with your test user ID
    test_user_id = "testuser123"

    asyncio.run(print_history(test_user_id))
