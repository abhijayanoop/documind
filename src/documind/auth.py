from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from documind.config import settings
import jwt

@dataclass
class Principal:
    user_id: str
    tenant_id: str
    role: str

class AuthError(Exception):
    """Raised when a token is missing, malformed, expired, or tampered."""

def create_access_token(user_id: str, tenant_id: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expiry_minutes)
    }
    return jwt.encode(payload, settings.jwt_secret, settings.jwt_algorithm)

def decode_access_token(token: str) -> Principal:
    try:
        claim = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError:
        raise AuthError("token expired")
    except jwt.InvalidTokenError:
        raise AuthError("invalid token")
    
    try:
        return Principal(
            user_id=claim["sub"],
            tenant_id=claim["tenant_id"],
            role=claim["role"]
        )
    except KeyError as e:
        raise AuthError(f"Token missing claim: {e}")