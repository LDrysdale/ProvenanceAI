# firebase_auth.py

import os
from fastapi import APIRouter, HTTPException, Request, Response, Depends
from pydantic import BaseModel
from config import USE_LOCAL_DATA
from session_manager import create_session, clear_session, get_session_user, refresh_session

router = APIRouter()

if not USE_LOCAL_DATA:
    import firebase_admin
    from firebase_admin import auth, credentials

    cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "path/to/your/serviceAccountKey.json")
    cred = credentials.Certificate(cred_path)
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)

class TokenRequest(BaseModel):
    token: str

@router.post("/login")
async def login(request_data: TokenRequest, response: Response):
    if USE_LOCAL_DATA:
        raise HTTPException(status_code=403, detail="Firebase auth disabled in local mode")

    try:
        decoded_token = auth.verify_id_token(request_data.token)
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
    refresh_session(response, user)  # 👈 Extend session
    return user

@router.post("/logout")
async def logout(response: Response):
    clear_session(response)
    return {"message": "Logged out successfully"}
