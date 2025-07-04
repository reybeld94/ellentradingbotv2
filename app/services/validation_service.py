# backend/app/services/validation_service.py

import re
from typing import Dict


class ValidationService:

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validar formato de email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    @staticmethod
    def validate_username(username: str) -> Dict[str, any]:
        """Validar username"""
        errors = []

        if len(username) < 3:
            errors.append("Username must be at least 3 characters long")

        if len(username) > 30:
            errors.append("Username must be less than 30 characters")

        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            errors.append(
                "Username can only contain letters, numbers, hyphens and underscores"
            )

        if username.startswith('_') or username.startswith('-'):
            errors.append("Username cannot start with underscore or hyphen")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors
        }

    @staticmethod
    def validate_password(password: str) -> Dict[str, any]:
        """Validar password con reglas de seguridad"""
        errors = []
        strength_score = 0

        # Longitud mínima
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        else:
            strength_score += 1

        # Longitud máxima
        if len(password) > 128:
            errors.append("Password must be less than 128 characters")

        # Al menos una minúscula
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        else:
            strength_score += 1

        # Al menos una mayúscula
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        else:
            strength_score += 1

        # Al menos un número
        if not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
        else:
            strength_score += 1

        # Al menos un carácter especial
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        else:
            strength_score += 1

        # Determinar fuerza del password
        if strength_score <= 2:
            strength = "weak"
        elif strength_score <= 3:
            strength = "medium"
        elif strength_score <= 4:
            strength = "strong"
        else:
            strength = "very_strong"

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "strength": strength,
            "score": strength_score
        }

    @staticmethod
    def validate_registration_data(
        email: str, username: str, password: str
    ) -> Dict[str, any]:
        """Validar todos los datos de registro"""
        all_errors = []

        # Validar email
        if not ValidationService.validate_email(email):
            all_errors.append("Invalid email format")

        # Validar username
        username_validation = ValidationService.validate_username(username)
        if not username_validation["is_valid"]:
            all_errors.extend(username_validation["errors"])

        # Validar password
        password_validation = ValidationService.validate_password(password)
        if not password_validation["is_valid"]:
            all_errors.extend(password_validation["errors"])

        return {
            "is_valid": len(all_errors) == 0,
            "errors": all_errors,
            "password_strength": password_validation.get(
                "strength", "unknown"
            ),
        }


# Instancia global
validation_service = ValidationService()

