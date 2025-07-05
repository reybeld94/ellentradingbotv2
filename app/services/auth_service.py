# backend/app/services/auth_service.py

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.config import settings
from app.models.user import User
from app.schemas.auth import TokenData
import secrets

# Configuración de encriptación
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self):
        self.secret_key = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm
        self.access_token_expire_minutes = settings.jwt_access_token_expire_minutes

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verificar password"""
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Hashear password"""
        return pwd_context.hash(password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Crear JWT token"""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[TokenData]:
        """Verificar y decodificar JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            email: str = payload.get("sub")

            if email is None:
                return None

            token_data = TokenData(email=email)
            return token_data

        except JWTError:
            return None

    def authenticate_user(self, db: Session, email: str, password: str) -> Optional[User]:
        """Autenticar usuario"""
        user = db.query(User).filter(User.email == email).first()

        if not user:
            return None

        if not user.check_password(password):
            return None

        return user

    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        """Obtener usuario por email"""
        return db.query(User).filter(User.email == email).first()

    def get_user_by_username(self, db: Session, username: str) -> Optional[User]:
        """Obtener usuario por username"""
        return db.query(User).filter(User.username == username).first()

    def create_user(self, db: Session, email: str, username: str, password: str, full_name: str = None, position_limit: int = 7) -> User:
        """Crear nuevo usuario"""
        # Verificar si ya existe
        if self.get_user_by_email(db, email):
            raise ValueError("Email already registered")

        if self.get_user_by_username(db, username):
            raise ValueError("Username already taken")

        # Crear usuario
        user = User(
            email=email,
            username=username,
            full_name=full_name,
            position_limit=position_limit
        )
        user.set_password(password)
        user.generate_verification_token()

        db.add(user)
        db.commit()
        db.refresh(user)

        return user

    def update_last_login(self, db: Session, user: User):
        """Actualizar último login"""
        user.last_login = datetime.utcnow()
        db.commit()

    def generate_reset_token(self, db: Session, email: str) -> Optional[str]:
        """Generar token de reset de password"""
        user = self.get_user_by_email(db, email)
        if not user:
            return None

        reset_token = user.generate_reset_token()
        user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)  # 1 hora

        db.commit()
        return reset_token

    def reset_password(self, db: Session, token: str, new_password: str) -> bool:
        """Reset password con token"""
        user = db.query(User).filter(User.reset_token == token).first()

        if not user or not user.reset_token_expires:
            return False

        if datetime.utcnow() > user.reset_token_expires:
            return False

        # Actualizar password
        user.set_password(new_password)
        user.reset_token = None
        user.reset_token_expires = None

        db.commit()
        return True

    def verify_email(self, db: Session, token: str) -> bool:
        """Verificar email con token"""
        user = db.query(User).filter(User.verification_token == token).first()

        if not user:
            return False

        user.is_verified = True
        user.verification_token = None

        db.commit()
        return True


# Instancia global
auth_service = AuthService()
