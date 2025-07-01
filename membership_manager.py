# membership_manager.py

from firebase_admin import firestore
from datetime import datetime, timedelta
import pytz
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler

db = firestore.client()

async def renew_membership(user_id: str, tier: str):
    now = datetime.now(pytz.UTC)
    
    # Calculate expiry based on tier
    if tier == "free":
        expiry = now + timedelta(days=365*100)  # 100 years
        subscription_status = "lifetime"
    else:
        expiry = now + timedelta(days=365)  # 1 year
        subscription_status = "active"
    
    user_ref = db.collection("users").document(user_id)
    user_ref.update({
        "tier": tier,
        "subscriptionStatus": subscription_status,
        "createdAt": now,
        "membershipExpiry": expiry,
    })
    print(f"User {user_id} renewed with tier {tier} until {expiry.isoformat()}")

async def cancel_membership(user_id: str):
    user_ref = db.collection("users").document(user_id)
    user_ref.update({
        "subscriptionStatus": "Cancelled"
    })
    print(f"User {user_id} subscription cancelled.")

async def downgrade_expired_users():
    now = datetime.now(pytz.UTC)
    users_ref = db.collection("users")
    
    # Firestore queries are sync, so we run in a threadpool executor to not block asyncio loop
    loop = asyncio.get_event_loop()
    
    def query_expired():
        return list(users_ref.where("membershipExpiry", "<=", now).where("tier", "!=", "free").stream())
    
    expired_users = await loop.run_in_executor(None, query_expired)
    
    for user in expired_users:
        user_data = user.to_dict()
        user_id = user.id
        print(f"Downgrading expired user {user_id}")
        
        users_ref.document(user_id).update({
            "tier": "free",
            "subscriptionStatus": "lifetime",
            "createdAt": now,
            "membershipExpiry": now + timedelta(days=365*100)
        })
    return len(expired_users)

async def update_membership(user_id: str, new_tier: str):
    """
    Update a user's membership tier (upgrade from free or change between paid tiers).

    - Updates createdAt to now.
    - Updates membershipExpiry based on new tier.
    - Updates subscriptionStatus accordingly.
    """
    now = datetime.now(pytz.UTC)
    user_ref = db.collection("users").document(user_id)

    # Fetch user document
    user_snapshot = user_ref.get()
    if not user_snapshot.exists:
        raise ValueError(f"User {user_id} does not exist in Firestore")

    # Determine new expiry and subscription status
    if new_tier == "free":
        expiry = now + timedelta(days=365*100)
        subscription_status = "lifetime"
    else:
        expiry = now + timedelta(days=365)
        subscription_status = "active"

    # Update document with new membership data
    user_ref.update({
        "tier": new_tier,
        "subscriptionStatus": subscription_status,
        "createdAt": now,
        "membershipExpiry": expiry,
    })
    print(f"User {user_id} membership updated to {new_tier} until {expiry.isoformat()}")

# Scheduler setup
scheduler = AsyncIOScheduler(timezone=pytz.UTC)

def schedule_daily_membership_check():
    # Schedule to run every day at 00:00 UTC
    scheduler.add_job(downgrade_expired_users, "cron", hour=0, minute=0, id="daily_membership_check")
    scheduler.start()
    print("Scheduled daily membership expiry check at 00:00 UTC")

# Call this function once when your app starts, e.g., from main.py:
# from membership_manager import schedule_daily_membership_check
# schedule_daily_membership_check()
