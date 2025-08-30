import json
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, firestore

# -------------------------
# Initialize Firebase Admin with your service account
# -------------------------
cred_path = r"C:\Users\leodr\Desktop\ProvAIall\provenanceai-clean\credentials\firebase-adminsdk.json"
cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)

db = firestore.client()  # Firestore client

# -------------------------
# Tier durations
# -------------------------
TIER_DURATIONS = {
    "free": 365 * 100,  # 100 years
    "paid": 90,         # 3 months
}

# -------------------------
# Helper to calculate expiry
# -------------------------
def calculate_membership_expiry(tier: str) -> datetime:
    now = datetime.utcnow()
    days = TIER_DURATIONS.get(tier, 30)
    return now + timedelta(days=days)

# -------------------------
# Create or update Firestore user
# -------------------------
def create_firestore_user(
    uid: str,
    username: str,
    email: str,
    display_name: str = "",
    profile_pic_url: str = "",
    tier: str = "free",
    addon_psychologist: bool = False,
    addon_unlimited: bool = False
):
    try:
        now = datetime.utcnow()
        user_data = {
            "username": username,
            "email": email,
            "displayName": display_name,
            "profilePicURL": profile_pic_url,
            "tier": tier,
            "subscriptionStatus": "lifetime" if tier == "free" else "paid",
            "membershipExpiry": calculate_membership_expiry(tier),
            "addon_psychologist": addon_psychologist,
            "addon_psychologist_expiry": (now + timedelta(days=90) if addon_psychologist else None),
            "addon_unlimited": addon_unlimited,
            "addon_unlimited_expiry": (now + timedelta(days=90) if addon_unlimited else None),
            "createdAt": now
        }

        user_ref = db.collection("users").document(uid)
        user_ref.set(user_data, merge=True)
        print(f"Uploaded user: {uid} ({email})")
    except Exception as e:
        print(f"Error uploading user {uid}: {e}")

# -------------------------
# Batch upload from JSON
# -------------------------
def batch_upload_users_from_json(file_path: str):
    with open(file_path, "r") as f:
        users = json.load(f)

    for user in users:
        create_firestore_user(
            uid=user["uid"],
            username=user["username"],
            email=user["email"],
            display_name=user.get("display_name", ""),
            profile_pic_url=user.get("profile_pic_url", ""),
            tier=user.get("tier", "free"),
            addon_psychologist=user.get("addon_psychologist", False),
            addon_unlimited=user.get("addon_unlimited", False)
        )

    print("Batch upload completed!")

# -------------------------
# Main execution
# -------------------------
if __name__ == "__main__":
    json_file_path = r"C:\Users\leodr\Desktop\ProvAIall\provenanceai-clean\data_upload\firestoredata.json"
    batch_upload_users_from_json(json_file_path)

