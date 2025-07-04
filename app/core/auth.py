# backend/app/dependencies/auth.py

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.auth_service import auth_service
from ..models.user import User

# Configurar esquema de seguridad
security = HTTPBearer()


async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
) -> User:
    """Obtener usuario actual desde JWT token"""

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Verificar token
    token_data = auth_service.verify_token(credentials.credentials)
    if token_data is None:
        raise credentials_exception

    # Obtener usuario
    user = auth_service.get_user_by_email(db, email=token_data.email)
    if user is None:
        raise credentials_exception

    # Verificar que esté activo
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user"
        )

    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Obtener usuario activo"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_verified_user(current_user: User = Depends(get_current_user)) -> User:
    """Obtener usuario verificado"""
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified"
        )
    return current_user


async def get_admin_user(current_user: User = Depends(get_current_verified_user)) -> User:
    """Obtener usuario admin"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


# Dependencia opcional para rutas que pueden funcionar con o sin autenticación
async def get_current_user_optional(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
) -> User | None:
    """Obtener usuario actual (opcional)"""
    try:
        if not credentials:
            return None

        token_data = auth_service.verify_token(credentials.credentials)
        if token_data is None:
            return None

        user = auth_service.get_user_by_email(db, email=token_data.email)
        return user if user and user.is_active else None

    except Exception:
        return None

