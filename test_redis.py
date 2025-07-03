from dotenv import load_dotenv
import os
load_dotenv()

import asyncio
from redis_chat_history import store_chat_message, get_chat_history

async def test_redis_chat_history():
    user_id = "testuser123"
    question = "What is AI?"
    answer = "AI stands for Artificial Intelligence."

    # Store a chat message
    await store_chat_message(user_id, question, answer)
    print(f"Stored message for user {user_id}")

    # Retrieve chat history
    history = await get_chat_history(user_id, limit=10)
    print(f"Chat history for user {user_id}:")
    for msg in history:
        print(msg)

asyncio.run(test_redis_chat_history())
