# firebase_auth.py

import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from config import USE_LOCAL_DATA

router = APIRouter()

if not USE_LOCAL_DATA:
    import firebase_admin
    from firebase_admin import auth, credentials

    # Initialize Firebase Admin SDK only once
    cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "path/to/your/serviceAccountKey.json")
    cred = credentials.Certificate(cred_path)
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)

# Define request schema
class TokenRequest(BaseModel):
    token: str

@router.post("/verify_token")
async def verify_token(request_data: TokenRequest):
    if USE_LOCAL_DATA:
        raise HTTPException(status_code=403, detail="Firebase auth disabled in local mode")

    try:
        decoded_token = auth.verify_id_token(request_data.token)
        uid = decoded_token.get("uid")
        user_record = auth.get_user(uid)

        return {
            "uid": uid,
            "email": user_record.email,
            "name": user_record.display_name,
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
