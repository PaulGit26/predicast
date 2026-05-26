"""
JWT authentication: supports both Auth0 RS256 (production) and HS256 (local dev).
Auth0 RS256: validates against the tenant JWKS endpoint (no shared secret needed).
HS256: simple shared-secret JWT for local development / tests.
"""

from datetime import datetime, timedelta
from typing import Optional
import httpx

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)

# In-memory JWKS cache  {kid: public_key_pem}
_jwks_cache: dict = {}


class TokenPayload(BaseModel):
    sub: str
    org_id: str = ""
    scopes: list = []
    exp: datetime


# ── Password helpers ──────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── HS256 helpers (local dev) ─────────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    payload = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=settings.JWT_EXPIRATION_HOURS))
    payload["exp"] = expire
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")


def _decode_hs256(token: str) -> TokenPayload:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        sub = payload.get("sub") or ""
        org_id = payload.get("org_id") or ""
        return TokenPayload(
            sub=sub,
            org_id=org_id,
            scopes=payload.get("scopes", []),
            exp=datetime.fromtimestamp(payload["exp"]),
        )
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


# ── Auth0 RS256 helpers ───────────────────────────────────────────────────────

def _get_auth0_public_key(kid: str) -> str:
    """Fetch JWKS from Auth0 and return the RSA public key for given kid."""
    if kid in _jwks_cache:
        return _jwks_cache[kid]

    jwks_url = f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json"
    response = httpx.get(jwks_url, timeout=5)
    response.raise_for_status()
    jwks = response.json()

    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
            from cryptography.hazmat.backends import default_backend
            import base64, struct

            def _b64_to_int(val: str) -> int:
                data = base64.urlsafe_b64decode(val + "==")
                return int.from_bytes(data, "big")

            pub = RSAPublicNumbers(
                e=_b64_to_int(key["e"]),
                n=_b64_to_int(key["n"]),
            ).public_key(default_backend())

            from cryptography.hazmat.primitives.serialization import (
                Encoding, PublicFormat
            )
            pem = pub.public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo).decode()
            _jwks_cache[kid] = pem
            return pem

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Public key not found")


def _decode_auth0(token: str) -> TokenPayload:
    """Validate an Auth0 JWT (RS256) against the tenant JWKS."""
    try:
        unverified_header = jwt.get_unverified_header(token)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token header")

    kid = unverified_header.get("kid")
    if not kid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing kid in token")

    public_key = _get_auth0_public_key(kid)

    try:
        payload = jwt.decode(
            token,
            public_key,
            algorithms=settings.AUTH0_ALGORITHMS,
            audience=settings.AUTH0_API_AUDIENCE,
            issuer=f"https://{settings.AUTH0_DOMAIN}/",
        )
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))

    return TokenPayload(
        sub=payload.get("sub", ""),
        org_id=payload.get("org_id", ""),
        scopes=payload.get("permissions", payload.get("scope", "").split()),
        exp=datetime.fromtimestamp(payload["exp"]),
    )


# ── Main decode dispatcher ────────────────────────────────────────────────────

def decode_token(token: str) -> TokenPayload:
    """Decode JWT: use Auth0 RS256 when configured, HS256 otherwise (dev)."""
    if settings.AUTH0_DOMAIN and settings.AUTH0_API_AUDIENCE:
        return _decode_auth0(token)
    return _decode_hs256(token)


# ── FastAPI dependencies ──────────────────────────────────────────────────────

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> TokenPayload:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    return decode_token(credentials.credentials)


async def get_current_org(current_user: TokenPayload = Depends(get_current_user)) -> str:
    return current_user.org_id


class RBACChecker:
    def __init__(self, required_roles: list):
        self.required_roles = required_roles

    async def __call__(self, current_user: TokenPayload = Depends(get_current_user)) -> TokenPayload:
        for role in self.required_roles:
            if role not in current_user.scopes:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required role: {role}",
                )
        return current_user
