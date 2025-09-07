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

# Current time in UTC (timezone-aware)
now = datetime.datetime.now(datetime.timezone.utc)

for i, entry in enumerate(quotes, start=1):
    quote = entry["quote"]
    timestamp = entry["timestamp"]  # e.g., "2025-09-01T15:00:00Z"

    # Convert to timezone-aware datetime
    dt = datetime.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

    # Skip past posts
    if dt <= now:
        print(f"⏩ Skipping past timestamp: {timestamp} | Quote: {quote}")
        continue

    # Wait until the scheduled time
    wait_seconds = (dt - now).total_seconds()
    print(f"⏳ Waiting {wait_seconds:.0f} seconds until {timestamp}...")

    time.sleep(wait_seconds)

    try:
        response = client.create_tweet(text=quote)
        print(f"✅ {i} of {len(quotes)} --> Posted: '{quote}' at {dt}")
    except Exception as e:
        print(f"⚠️ Failed to post '{quote}' at {dt}: {e}")

    # Update "now" after posting
    now = datetime.datetime.now(datetime.timezone.utc)

    # Delay to avoid rate limiting
    time.sleep(5)
