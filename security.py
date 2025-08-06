from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException, Request
from firebase_admin import auth as firebase_auth
from typing import List

security = HTTPBearer()

async def get_user_id_from_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        decoded_token = firebase_auth.verify_id_token(token)
        return decoded_token["uid"]
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired Firebase token")

def require_role(required_roles: List[str]):
    def role_checker(request: Request):
        role = request.headers.get("X-User-Role")
        if role not in required_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return {"role": role}
    return role_checker