import os
import json
from fastapi import APIRouter, HTTPException, Request, Response, Depends, Form
from pydantic import BaseModel
from config import USE_LOCAL_DATA  # Make sure this is set in your config
from session_manager import create_session, clear_session, get_session_user, refresh_session

router = APIRouter()

MOCK_USERS_FILE = "tests/datasets/mock_users.json"  # Path to your mock users file

def load_mock_users():
    """Loads the mock users from a local JSON file."""
    try:
        with open(MOCK_USERS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []

# If using Firebase, initialize the SDK
if not USE_LOCAL_DATA:
    import firebase_admin
    from firebase_admin import auth, credentials, firestore

    cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "path/to/your/serviceAccountKey.json")
    cred = credentials.Certificate(cred_path)
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
    db = firestore.client()  # Firestore client for Firebase interaction

class TokenRequest(BaseModel):
    token: str

# For local mock user authentication
class LoginForm(BaseModel):
    email: str
    password: str

@router.post("/login")
async def login(response: Response, token_request: TokenRequest = None, email: str = Form(None), password: str = Form(None)):
    """
    Login endpoint that supports:
    - Firebase login with token when USE_LOCAL_DATA = 0
    - Mock user login with email/password form when USE_LOCAL_DATA = 1
    """
    if USE_LOCAL_DATA:
        # Use local mock user login logic (email/password match)
        if not email or not password:
            raise HTTPException(status_code=400, detail="Email and password are required")

        # Load mock users
        users = load_mock_users()
        matched_user = None
        for u in users:
            if u.get("email") == email and u.get("password") == password:
                matched_user = u
                break

        if not matched_user:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        # Prepare session user data without password
        user_data = {
            "uid": matched_user.get("uid"),
            "email": matched_user.get("email"),
            "name": matched_user.get("name"),
            "role": matched_user.get("role", "user"),  # Default to "user"
        }
        create_session(response, user_data)
        return user_data

    else:
        # Firebase token login mode
        if token_request is None:
            raise HTTPException(status_code=400, detail="Token is required")

        try:
            # Verify Firebase token
            decoded_token = auth.verify_id_token(token_request.token)
            uid = decoded_token.get("uid")
            user_record = auth.get_user(uid)

            # Optionally, get user from Firestore (if you want more info than what Firebase gives)
            user_ref = db.collection("users").document(uid)
            user_doc = user_ref.get()
            if user_doc.exists:
                user_data = user_doc.to_dict()
            else:
                # Fallback to Firebase user record
                user_data = {
                    "uid": uid,
                    "email": user_record.email,
                    "name": user_record.display_name,
                    "role": decoded_token.get("role", "user"),  # Optional custom claim
                }

            # Create session for the logged-in user
            create_session(response, user_data)
            return user_data

        except Exception as e:
            raise HTTPException(status_code=401, detail=str(e))

@router.get("/me")
async def me(request: Request, response: Response, user=Depends(get_session_user)):
    """Get the current logged-in user details."""
    refresh_session(response, user)  # Extend session duration
    return user

@router.post("/logout")
async def logout(response: Response):
    """Logout the user by clearing the session."""
    clear_session(response)
    return {"message": "Logged out successfully"}
