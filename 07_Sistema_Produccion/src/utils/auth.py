"""
Authentication & JWT utilities
"""

import os
from datetime import datetime, timedelta
from typing import Dict, Optional
import jwt
from jwt import PyJWTError
import logging

logger = logging.getLogger(__name__)

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", 24))


class TokenManager:
    """Gestiona creación y validación de JWT tokens"""
    
    @staticmethod
    def create_token(
        user_id: str,
        tenant_id: str,
        email: str,
        is_admin: bool = False,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Crea un JWT token
        
        Args:
            user_id: ID del usuario
            tenant_id: ID del tenant/empresa
            email: Email del usuario
            is_admin: Si es administrador
            expires_delta: Timedelta personalizado de expiración
        
        Returns:
            Token JWT
        """
        payload = {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "email": email,
            "is_admin": is_admin,
            "iat": datetime.utcnow(),
        }
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
        
        payload["exp"] = expire
        
        try:
            encoded_jwt = jwt.encode(
                payload,
                JWT_SECRET,
                algorithm=JWT_ALGORITHM
            )
            logger.info(f"✅ Token creado para usuario {email}")
            return encoded_jwt
        except Exception as e:
            logger.error(f"❌ Error creando token: {e}")
            raise
    
    @staticmethod
    def verify_token(token: str) -> Dict:
        """
        Verifica y decodifica un JWT token
        
        Args:
            token: Token JWT
        
        Returns:
            Payload decodificado
        
        Raises:
            PyJWTError: Si el token es inválido
        """
        try:
            payload = jwt.decode(
                token,
                JWT_SECRET,
                algorithms=[JWT_ALGORITHM]
            )
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("⚠️ Token expirado")
            raise PyJWTError("Token expirado")
        except jwt.InvalidTokenError as e:
            logger.warning(f"⚠️ Token inválido: {e}")
            raise PyJWTError("Token inválido")
    
    @staticmethod
    def extract_token_from_header(auth_header: Optional[str]) -> Optional[str]:
        """
        Extrae el token del header Authorization
        
        Args:
            auth_header: Header "Authorization: Bearer <token>"
        
        Returns:
            Token o None
        """
        if not auth_header:
            return None
        
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None
        
        return parts[1]


# Para password hashing (simplificado en MVP, usar bcrypt en prod)
def hash_password(password: str) -> str:
    """Hash de contraseña (MVP simplificado)"""
    # En producción usar bcrypt o argon2
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica contraseña"""
    return hash_password(plain_password) == hashed_password
