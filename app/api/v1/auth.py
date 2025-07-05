# backend/app/api/v1/auth.py

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Any

from app.database import get_db
from app.schemas.auth import (
    UserCreate, UserLogin, UserResponse, Token,
    PasswordReset, PasswordResetConfirm, UserUpdate
)
from typing import Any, Dict
from app.services.auth_service import auth_service
from app.services.validation_service import validation_service
from app.core.auth import get_current_user, get_current_verified_user
from app.utils.responses import AuthResponses
from app.models.user import User

router = APIRouter()
security = HTTPBearer()


@router.post("/register", response_model=Dict[str, Any])  # CORREGIR ESTO
async def register(
        user_data: UserCreate,
        db: Session = Depends(get_db)
):
    """Registrar nuevo usuario"""

    print(f"🔄 Registration attempt: {user_data.dict()}")  # DEBUG

    # Validar datos de entrada
    validation = validation_service.validate_registration_data(
        user_data.email,
        user_data.username,
        user_data.password
    )

    print(f"📊 Validation result: {validation}")  # DEBUG

    if not validation["is_valid"]:
        print(f"❌ Validation failed: {validation['errors']}")  # DEBUG
        AuthResponses.validation_error(validation["errors"])

    try:
        # Crear usuario
        user = auth_service.create_user(
            db=db,
            email=user_data.email,
            username=user_data.username,
            password=user_data.password,
            full_name=user_data.full_name,
            position_limit=user_data.position_limit
        )

        print(f"✅ User created: {user.username}")  # DEBUG

        return AuthResponses.success_response(
            message="User registered successfully. Please verify your email.",
            data={
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "verification_required": True,
                "password_strength": validation["password_strength"]
            }
        )

    except ValueError as e:
        print(f"❌ ValueError: {e}")  # DEBUG
        if "Email already registered" in str(e):
            AuthResponses.user_already_exists()
        elif "Username already taken" in str(e):
            AuthResponses.username_taken()
        else:
            raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"💥 Unexpected error: {e}")  # DEBUG
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/login", response_model=Token)
async def login(
        user_credentials: UserLogin,
        db: Session = Depends(get_db)
):
    """Iniciar sesión"""

    # Autenticar usuario
    user = auth_service.authenticate_user(
        db,
        user_credentials.email,
        user_credentials.password
    )

    if not user:
        AuthResponses.invalid_credentials()

    if not user.is_active:
        AuthResponses.inactive_user()

    # Crear token de acceso
    access_token_expires = timedelta(minutes=auth_service.access_token_expire_minutes)
    access_token = auth_service.create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )

    # Actualizar último login
    auth_service.update_last_login(db, user)

    # Preparar respuesta del usuario
    user_response = UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        is_active=user.is_active,
        is_verified=user.is_verified,
        is_admin=user.is_admin,
        created_at=user.created_at,
        last_login=user.last_login,
        position_limit=user.position_limit
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=auth_service.access_token_expire_minutes * 60,  # en segundos
        user=user_response
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
        current_user: User = Depends(get_current_user)
):
    """Obtener información del usuario actual"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        is_admin=current_user.is_admin,
        created_at=current_user.created_at,
        last_login=current_user.last_login,
        position_limit=current_user.position_limit
    )


@router.put("/me", response_model=UserResponse)
async def update_profile(
        user_update: UserUpdate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Actualizar perfil del usuario"""

    # Verificar si el email ya existe (si se está cambiando)
    if user_update.email and user_update.email != current_user.email:
        existing_user = auth_service.get_user_by_email(db, user_update.email)
        if existing_user:
            AuthResponses.user_already_exists()

        # Si se cambia email, marcar como no verificado
        current_user.email = user_update.email
        current_user.is_verified = False
        current_user.generate_verification_token()

    # Actualizar nombre completo
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name

    if user_update.position_limit is not None:
        current_user.position_limit = user_update.position_limit

    db.commit()
    db.refresh(current_user)

    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        is_admin=current_user.is_admin,
        created_at=current_user.created_at,
        last_login=current_user.last_login,
        position_limit=current_user.position_limit
    )


@router.post("/verify-email/{token}")
async def verify_email(
        token: str,
        db: Session = Depends(get_db)
):
    """Verificar email con token"""

    success = auth_service.verify_email(db, token)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )

    return AuthResponses.success_response("Email verified successfully")


@router.post("/forgot-password")
async def forgot_password(
        password_reset: PasswordReset,
        db: Session = Depends(get_db)
):
    """Solicitar reset de password"""

    reset_token = auth_service.generate_reset_token(db, password_reset.email)

    if reset_token:
        # En producción, enviar email aquí
        # Por ahora solo devolvemos el token para testing
        return AuthResponses.success_response(
            "Password reset instructions sent to your email",
            data={"reset_token": reset_token}  # Solo para desarrollo
        )
    else:
        # No revelar si el email existe o no por seguridad
        return AuthResponses.success_response(
            "If the email exists, you will receive reset instructions"
        )


@router.post("/reset-password")
async def reset_password(
        password_reset_confirm: PasswordResetConfirm,
        db: Session = Depends(get_db)
):
    """Confirmar reset de password"""

    # Validar nueva contraseña
    password_validation = validation_service.validate_password(
        password_reset_confirm.new_password
    )

    if not password_validation["is_valid"]:
        AuthResponses.validation_error(password_validation["errors"])

    # Resetear password
    success = auth_service.reset_password(
        db,
        password_reset_confirm.token,
        password_reset_confirm.new_password
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    return AuthResponses.success_response("Password reset successfully")


@router.post("/refresh-token", response_model=Token)
async def refresh_token(
        current_user: User = Depends(get_current_user)
):
    """Renovar token de acceso"""

    # Crear nuevo token
    access_token_expires = timedelta(minutes=auth_service.access_token_expire_minutes)
    access_token = auth_service.create_access_token(
        data={"sub": current_user.email},
        expires_delta=access_token_expires
    )

    user_response = UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        is_admin=current_user.is_admin,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=auth_service.access_token_expire_minutes * 60,
        user=user_response
    )


@router.post("/logout")
async def logout():
    """Cerrar sesión (logout del lado cliente)"""
    # En JWT stateless, el logout se maneja del lado del cliente
    # eliminando el token del localStorage/sessionStorage
    return AuthResponses.success_response(
        "Logged out successfully. Please remove the token from client storage."
    )


@router.delete("/me")
async def delete_account(
        current_user: User = Depends(get_current_verified_user),
        db: Session = Depends(get_db)
):
    """Eliminar cuenta de usuario"""

    # Marcar como inactivo en lugar de eliminar (soft delete)
    current_user.is_active = False
    current_user.email = f"deleted_{current_user.id}@deleted.com"

    db.commit()

    return AuthResponses.success_response("Account deactivated successfully")


# Endpoints administrativos
@router.get("/users", response_model=list[UserResponse])
async def list_users(
        skip: int = 0,
        limit: int = 100,
        current_user: User = Depends(get_current_verified_user),
        db: Session = Depends(get_db)
):
    """Listar usuarios (solo para admin o el propio usuario)"""

    if current_user.is_admin:
        # Admin puede ver todos los usuarios
        users = db.query(User).offset(skip).limit(limit).all()
    else:
        # Usuario normal solo puede verse a sí mismo
        users = [current_user]

    return [UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        is_active=user.is_active,
        is_verified=user.is_verified,
        is_admin=user.is_admin,
        created_at=user.created_at,
        last_login=user.last_login
    ) for user in users]

