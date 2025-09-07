import json
from datetime import datetime, timedelta
from quotes_lists import QUOTES1

# List of quotes (add as many as you like)
QUOTES = QUOTES1


def generate_quotes_json(start_date: str, days: int, post_time: str = "15:00:00", filename="quotes.json"):
    """
    Generate a JSON file with scheduled quotes.

    Args:
        start_date (str): starting date in format YYYY-MM-DD
        days (int): number of days to generate
        post_time (str): time of posting in HH:MM:SS (UTC)
        filename (str): output filename
    """
    start_dt = datetime.fromisoformat(start_date)

    schedule = []
    for i in range(days):
        date = start_dt + timedelta(days=i)
        timestamp = f"{date.date()}T{post_time}Z"
        quote = QUOTES[i % len(QUOTES)]  # cycle quotes if fewer than days
        schedule.append({"timestamp": timestamp, "quote": quote})

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(schedule, f, indent=2, ensure_ascii=False)

    print(f"✅ Generated {filename} with {days} entries.")


if __name__ == "__main__":
    # Example: start on 2025-09-01, generate 90 days
    generate_quotes_json("2025-09-01", days=90, post_time="15:00:00")
