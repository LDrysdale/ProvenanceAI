from datetime import datetime, timedelta, timezone
from firebase_admin import firestore

# -------------------------
# Configurable Tier Durations
# -------------------------
TIER_DURATIONS = {
    "free": 365 * 100,   # 100 years
    "paid": 90,          # 3 months
    "premium": 365,      # 1 year
    "trial": 14,         # 2 weeks
}

# -------------------------
# Helper Functions
# -------------------------
def calculate_membership_expiry(tier: str) -> firestore.Timestamp:
    """Returns a Firestore Timestamp for when the membership should expire."""
    now = datetime.utcnow()
    duration_days = TIER_DURATIONS.get(tier, 30)  # Default 30 days
    expiry_date = now + timedelta(days=duration_days)
    return firestore.Timestamp.from_datetime(expiry_date)

# -------------------------
# User Creation / Update
# -------------------------
def update_user_subscription(
    uid: str,
    tier: str,
    email: str,
    display_name: str = "",
    profile_pic_url: str = "",
    addon_psychologist: bool = False,
    addon_unlimited: bool = False
):
    db = firestore.client()
    user_ref = db.collection("users").document(uid)
    expiry_timestamp = calculate_membership_expiry(tier)

    now = datetime.utcnow()
    user_data = {
        "email": email,
        "tier": tier,
        "displayName": display_name,
        "profilePicURL": profile_pic_url,
        "subscriptionStatus": "lifetime" if tier == "free" else "paid",
        "membershipExpiry": expiry_timestamp,
        "addon_psychologist": addon_psychologist,
        "addon_psychologist_expiry": (firestore.Timestamp.from_datetime(now + timedelta(days=90))
                                      if addon_psychologist else None),
        "addon_unlimited": addon_unlimited,
        "addon_unlimited_expiry": (firestore.Timestamp.from_datetime(now + timedelta(days=90))
                                   if addon_unlimited else None),
        "createdAt": firestore.SERVER_TIMESTAMP
    }

    user_ref.set(user_data, merge=True)

# -------------------------
# Upgrade User on Payment
# -------------------------
def upgrade_user_payment(
    uid: str,
    new_tier: str,
    activate_psychologist: bool = False,
    activate_unlimited: bool = False
):
    db = firestore.client()
    user_ref = db.collection("users").document(uid)
    user_doc = user_ref.get()

    if not user_doc.exists:
        raise ValueError("User not found")

    user_data = user_doc.to_dict()
    expiry_timestamp = calculate_membership_expiry(new_tier)
    now = datetime.utcnow()

    update_data = {
        "tier": new_tier,
        "subscriptionStatus": "paid",
        "membershipExpiry": expiry_timestamp,
    }

    # Activate add-ons with 3-month expiry if specified
    if activate_psychologist:
        update_data["addon_psychologist"] = True
        update_data["addon_psychologist_expiry"] = firestore.Timestamp.from_datetime(now + timedelta(days=90))
    if activate_unlimited:
        update_data["addon_unlimited"] = True
        update_data["addon_unlimited_expiry"] = firestore.Timestamp.from_datetime(now + timedelta(days=90))

    user_ref.update(update_data)

# -------------------------
# Check and Downgrade Expired Memberships
# -------------------------
def check_and_downgrade_user(uid: str):
    db = firestore.client()
    user_ref = db.collection("users").document(uid)
    user_doc = user_ref.get()

    if not user_doc.exists:
        return {"status": "not_found"}

    user_data = user_doc.to_dict()
    expiry = user_data.get("membershipExpiry")

    if expiry and expiry.to_datetime() < datetime.now(timezone.utc):
        # Expired → downgrade to free
        user_ref.update({
            "tier": "free",
            "subscriptionStatus": "lifetime",
            "membershipExpiry": datetime.utcnow() + timedelta(days=365*100)
        })
        return {"status": "downgraded", "new_tier": "free"}

    return {"status": "active", "tier": user_data.get("tier")}

# -------------------------
# Deactivate Expired Add-ons
# -------------------------
def deactivate_expired_addons(uid: str):
    db = firestore.client()
    user_ref = db.collection("users").document(uid)
    user_doc = user_ref.get()

    if not user_doc.exists:
        return {"status": "not_found"}

    user_data = user_doc.to_dict()
    now = datetime.utcnow()
    update_needed = {}

    # Psychologist add-on
    if user_data.get("addon_psychologist") and user_data.get("addon_psychologist_expiry"):
        if user_data["addon_psychologist_expiry"].to_datetime() < now:
            update_needed["addon_psychologist"] = False
            update_needed["addon_psychologist_expiry"] = None

    # Unlimited add-on
    if user_data.get("addon_unlimited") and user_data.get("addon_unlimited_expiry"):
        if user_data["addon_unlimited_expiry"].to_datetime() < now:
            update_needed["addon_unlimited"] = False
            update_needed["addon_unlimited_expiry"] = None

    if update_needed:
        user_ref.update(update_needed)
        return {"status": "addons_deactivated", "updates": update_needed}

    return {"status": "no_changes"}

# -------------------------
# Access Check Helper
# -------------------------
def can_access_feature(uid: str, feature: str) -> bool:
    """
    Checks if a user can access a feature/add-on.
    feature: 'tier' or 'psychologist' or 'unlimited'
    """
    db = firestore.client()
    user_ref = db.collection("users").document(uid)
    user_doc = user_ref.get()

    if not user_doc.exists:
        return False

    user_data = user_doc.to_dict()
    now = datetime.utcnow()

    # Check tier access
    if feature == "tier":
        expiry = user_data.get("membershipExpiry")
        if expiry and expiry.to_datetime() > now:
            return True
        # Free tier always active
        if user_data.get("tier") == "free":
            return True
        return False

    # Check add-on access
    addon_active = user_data.get(f"addon_{feature}", False)
    addon_expiry = user_data.get(f"addon_{feature}_expiry")
    if addon_active and addon_expiry and addon_expiry.to_datetime() > now:
        return True

    return False
