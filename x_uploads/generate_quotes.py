import json
from datetime import datetime, timedelta, timezone
from quotes_lists import QUOTES1
import random

# List of quotes (add as many as you like)
QUOTES = QUOTES1


# Big list of hashtags to choose from
HASHTAGS = [
    "#wisdom", "#inspiration", "#motivation", "#LifeLessons", "#mindset",
    "#MondayMotivation", "#GoalSetting", "#DreamBig", "#quotes", "#leadership",
    "#discipline", "#courage", "#strategy", "#selfgrowth", "#resilience",
    "#warriormindset", "#AncientWisdom", "#dailyquote", "#strength", "#focus", "#PositiveVibes",
    "#KeepPushing", "#power","#StayFocused","#StayPositive","#positivity","#selfimprovement",
    "#entrepreneurship","#PurposeDriven","#motivationalquotes","#lifestyle","#successmindset",
    "#selfdiscipline","#hustle","#grind","#nevergiveup","#believeinyourself","#mindfulness",
    "#selfcare","#mentalhealth","#growthmindset","#selflove","#confidence","#determination",
    "#ambition","#inspire","#leadershipquotes","#businessquotes","#successquotes",
]

def generate_quotes_json(start_date: str, days: int, post_time: str = "15:00:00", filename="quotes.json"):
    start_dt = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)

    schedule = []
    for i in range(days):
        date = start_dt + timedelta(days=i)
        hour, minute, second = map(int, post_time.split(":"))
        dt = date.replace(hour=hour, minute=minute, second=second, microsecond=0)
        timestamp = dt.isoformat().replace("+00:00", "Z")

        quote = QUOTES[i % len(QUOTES)]

        # Try adding hashtags until we risk going over 280 characters
        random.shuffle(HASHTAGS)
        hashtags_to_add = []
        for tag in HASHTAGS:
            test_post = f"{quote}\n\n{' '.join(hashtags_to_add + [tag])}".strip()
            if len(test_post) <= 280:
                hashtags_to_add.append(tag)
            else:
                break

        full_post = f"{quote}\n\n{' '.join(hashtags_to_add)}"
        schedule.append({"timestamp": timestamp, "quote": full_post})

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(schedule, f, indent=2, ensure_ascii=False)

    print(f"✅ Generated {filename} with {days} entries (quotes + hashtags, capped at 280 chars).")

if __name__ == "__main__":
    generate_quotes_json("2025-09-01", days=90, post_time="15:00:00")
