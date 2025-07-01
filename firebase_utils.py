from datetime import datetime, timedelta
from firebase_admin import firestore

def calculate_membership_expiry(tier: str) -> firestore.Timestamp:
    now = datetime.utcnow()
    if tier == "free":
        expiry_date = now + timedelta(days=365 * 100)  # 100 years
    else:
        expiry_date = now + timedelta(days=365)  # 1 year
    return firestore.Timestamp.from_datetime(expiry_date)

def update_user_subscription(uid: str, tier: str, email: str, display_name: str = "", profile_pic_url: str = ""):
    db = firestore.client()
    user_ref = db.collection("users").document(uid)
    expiry_timestamp = calculate_membership_expiry(tier)

    user_data = {
        "email": email,
        "tier": tier,
        "displayName": display_name,
        "profilePicURL": profile_pic_url,
        "subscriptionStatus": "lifetime" if tier == "free" else "active",
        "membershipExpiry": expiry_timestamp,
        "createdAt": firestore.SERVER_TIMESTAMP,
    }
    user_ref.set(user_data, merge=True)
