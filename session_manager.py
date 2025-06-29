# session_manager.py

import os
import json
from fastapi import Request, Response, HTTPException
from itsdangerous import TimestampSigner, BadSignature, SignatureExpired

COOKIE_NAME = "session_token"
SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "super-secret-key")
signer = TimestampSigner(SECRET_KEY)

SESSION_DURATION_SECONDS = 1800  # 30 minutes

def create_session(response: Response, user_data: dict):
    payload = json.dumps(user_data)
    signed_data = signer.sign(payload.encode("utf-8"))

    response.set_cookie(
        key=COOKIE_NAME,
        value=signed_data.decode("utf-8"),
        max_age=SESSION_DURATION_SECONDS,
        httponly=True,
        secure=True,       # ✅ Secure in production
        samesite="Lax",
        path="/"
    )

def get_session_user(request: Request) -> dict:
    cookie = request.cookies.get(COOKIE_NAME)
    if not cookie:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        unsigned = signer.unsign(cookie, max_age=SESSION_DURATION_SECONDS)
        user_data = json.loads(unsigned.decode("utf-8"))
        return user_data
    except SignatureExpired:
        raise HTTPException(status_code=401, detail="Session expired")
    except BadSignature:
        raise HTTPException(status_code=401, detail="Invalid session")

def refresh_session(response: Response, user_data: dict):
    # Called after any authenticated access to extend session
    create_session(response, user_data)

def clear_session(response: Response):
    response.delete_cookie(COOKIE_NAME)
