# firebase_auth.py

import os
import json
from fastapi import APIRouter, HTTPException, Request, Response, Depends, Form
from pydantic import BaseModel
from config import USE_LOCAL_DATA
from session_manager import create_session, clear_session, get_session_user, refresh_session

router = APIRouter()

MOCK_USERS_FILE = "tests/datasets/mock_users.json"

def load_mock_users():
    try:
        with open(MOCK_USERS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []

if not USE_LOCAL_DATA:
    import firebase_admin
    from firebase_admin import auth, credentials

    cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "path/to/your/serviceAccountKey.json")
    cred = credentials.Certificate(cred_path)
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)

class TokenRequest(BaseModel):
    token: str

# For local mode: simple form login with email and password fields (adjust as needed)
class LoginForm(BaseModel):
    email: str
    password: str

@router.post("/login")
async def login(response: Response, token_request: TokenRequest = None, email: str = Form(None), password: str = Form(None)):
    """
    Login endpoint supports:
    - Firebase login with token when USE_LOCAL_DATA=0
    - Mock user login with email/password form when USE_LOCAL_DATA=1
    """
    if USE_LOCAL_DATA:
        # Validate mock user login
        if not email or not password:
            raise HTTPException(status_code=400, detail="Email and password required")

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
            "role": matched_user.get("role", "user"),
        }
        create_session(response, user_data)
        return user_data

    else:
        # Firebase token login mode
        if token_request is None:
            raise HTTPException(status_code=400, detail="Token required")

        try:
            decoded_token = auth.verify_id_token(token_request.token)
            uid = decoded_token.get("uid")
            user_record = auth.get_user(uid)

            user_data = {
                "uid": uid,
                "email": user_record.email,
                "name": user_record.display_name,
                "role": decoded_token.get("role", "user"),  # Optional custom claim
            }

            create_session(response, user_data)
            return user_data

        except Exception as e:
            raise HTTPException(status_code=401, detail=str(e))

@router.get("/me")
async def me(request: Request, response: Response, user=Depends(get_session_user)):
    refresh_session(response, user)  # Extend session duration
    return user

@router.post("/logout")
async def logout(response: Response):
    clear_session(response)
    return {"message": "Logged out successfully"}
