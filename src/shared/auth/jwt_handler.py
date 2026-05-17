"""
Utilidades de autenticación con JWT y RBAC.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.config import settings


# Configurar contexto de hash de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


class TokenPayload(BaseModel):
    """Payload del JWT."""
    sub: str  # user_id o tenant_id
    org_id: str
    scopes: list = []
    exp: datetime


def hash_password(password: str) -> str:
    """Hash de contraseña con bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica contraseña contra hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Crea un JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def decode_token(token: str) -> TokenPayload:
    """Decodifica y valida un JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str = payload.get("sub")
        org_id: str = payload.get("org_id")
        
        if user_id is None or org_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        return TokenPayload(
            sub=user_id,
            org_id=org_id,
            scopes=payload.get("scopes", []),
            exp=datetime.fromtimestamp(payload.get("exp"))
        )
    
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenPayload:
    """FastAPI dependency para obtener usuario actual del JWT."""
    return decode_token(credentials.credentials)


async def get_current_org(current_user: TokenPayload = Depends(get_current_user)) -> str:
    """Obtiene org_id del usuario actual."""
    return current_user.org_id


class RBACChecker:
    """Verificador de permisos basado en roles."""
    
    def __init__(self, required_roles: list):
        self.required_roles = required_roles
    
    async def __call__(self, current_user: TokenPayload = Depends(get_current_user)) -> TokenPayload:
        for role in self.required_roles:
            if role not in current_user.scopes:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required role: {role}"
                )
        return current_user
