import tweepy
import os
import json
import datetime
import time

# Authenticate with X API
client = tweepy.Client(
    consumer_key=os.getenv("CONSUMER_KEY"),
    consumer_secret=os.getenv("CONSUMER_SECRET"),
    access_token=os.getenv("ACCESS_TOKEN"),
    access_token_secret=os.getenv("ACCESS_SECRET")
)

# Load scheduled posts from JSON
with open("quotes.json", "r", encoding="utf-8") as f:
    quotes = json.load(f)

# Current time in UTC
now = datetime.datetime.utcnow()

for entry in quotes:
    quote = entry["quote"]
    timestamp = entry["timestamp"]  # e.g., "2025-09-01T15:00:00Z"

    # Convert to datetime
    dt = datetime.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

    # Skip past posts
    if dt <= now:
        print(f"⏩ Skipping past timestamp: {timestamp} | Quote: {quote}")
        continue

    # Convert to RFC3339 (required by X API)
    scheduled_at = dt.isoformat("T") + "Z"

    try:
        response = client.create_tweet(
            text=quote,
            scheduled_at=scheduled_at
        )
        print(f"✅ Scheduled: '{quote}' at {scheduled_at}")
    except Exception as e:
        print(f"⚠️ Failed to schedule '{quote}' at {scheduled_at}: {e}")

    # Delay to avoid rate limiting
    time.sleep(5)
