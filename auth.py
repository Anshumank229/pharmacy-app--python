import os
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, Header
from jose import JWTError, jwt

JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB

_MAGIC = {
    b"\xff\xd8\xff":       "image/jpeg",
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"%PDF":               "application/pdf",
}

def create_access_token(email: str, is_admin: bool) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {"sub": email, "is_admin": is_admin, "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def get_current_user(authorization: str = Header(...)) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header must be 'Bearer <token>'")
    token = authorization[len("Bearer "):]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("sub") is None:
            raise ValueError
        return payload
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid or expired token: {e}")

def get_current_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required.")
    return current_user

def validate_upload(file_bytes: bytes) -> str:
    if len(file_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large. Maximum 5 MB allowed.")
    for magic, content_type in _MAGIC.items():
        if file_bytes[:len(magic)] == magic:
            return content_type
    raise HTTPException(status_code=400, detail="Invalid file. Only real JPEG, PNG, or PDF accepted.")