import tweepy
import os
import json
import datetime

# Authenticate with X API
client = tweepy.Client(
    consumer_key=os.getenv("CONSUMER_KEY"),
    consumer_secret=os.getenv("CONSUMER_SECRET"),
    access_token=os.getenv("ACCESS_TOKEN"),
    access_token_secret=os.getenv("ACCESS_SECRET")
)

# Load scheduled posts from JSON
with open("x_uploads/quotes.json", "r", encoding="utf-8") as f:
    quotes = json.load(f)

# Current UTC date
now = datetime.datetime.now(datetime.timezone.utc)

for i, entry in enumerate(quotes, start=1):
    quote = entry["quote"]
    timestamp = entry["timestamp"]  # e.g., "2025-09-01T15:00:00Z"

    # Convert to timezone-aware datetime
    dt = datetime.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

    # Only post if the date matches today (UTC)
    if dt.date() != now.date():
        print(f"⏩ Skipping quote scheduled for {dt.date()}: '{quote}'")
        continue

    try:
        response = client.create_tweet(text=quote)
        print(f"✅ Posted {i} of {len(quotes)}: '{quote}' at {now}")
    except Exception as e:
        print(f"⚠️ Failed to post '{quote}' at {now}: {e}")
