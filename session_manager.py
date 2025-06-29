# session_manager.py
import json
from fastapi import Request, HTTPException, Response
from config import USE_LOCAL_DATA
import uuid
import time

MOCK_USERS_FILE = "tests/datasets/mock_users.json"

# Simple in-memory session store: { session_id: { "user_id": ..., "expires": ... } }
_sessions = {}

SESSION_DURATION_SECONDS = 3600  # 1 hour session expiry

async def create_session(user_id: str) -> str:
    """Create a new session ID for a user and store it in-memory."""
    session_id = str(uuid.uuid4())
    expires = time.time() + SESSION_DURATION_SECONDS
    _sessions[session_id] = {"user_id": user_id, "expires": expires}
    return session_id

async def get_session_user(request: Request):
    """Get user info from session or mock user headers."""
    if USE_LOCAL_DATA:
        # In local mode, expect header "X-User-Id" to identify mock user
        user_id = request.headers.get("X-User-Id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Missing X-User-Id header in local mode")

        try:
            with open(MOCK_USERS_FILE, "r") as f:
                users = json.load(f)
        except Exception as e:
            raise HTTPException(status_code=500, detail="Failed to load mock users")

        # Find user by id or email
        user = next((u for u in users if str(u.get("id")) == user_id or u.get("email") == user_id), None)
        if not user:
            raise HTTPException(status_code=401, detail="User not found in mock users")
        return user

    else:
        # Real Firebase auth logic here
        from firebase_admin import auth
        authorization = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Unauthorized")

        id_token = authorization.split(" ")[1]
        try:
            decoded_token = auth.verify_id_token(id_token)
            user_info = {
                "uid": decoded_token.get("uid"),
                "email": decoded_token.get("email"),
                "role": decoded_token.get("role", "reader")
            }
            return user_info
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid token")

async def clear_session(response: Response, session_id: str = None):
    """Clear the session by deleting session cookie and removing from store."""
    if session_id and session_id in _sessions:
        del _sessions[session_id]
    response.delete_cookie("session")

async def refresh_session(session_id: str):
    """Refresh session expiry if session exists."""
    session = _sessions.get(session_id)
    if session:
        session["expires"] = time.time() + SESSION_DURATION_SECONDS
