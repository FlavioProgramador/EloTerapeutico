"""
apps/users/managers.py
Manager customizado para o modelo de usuário do Elo Terapêutico.
"""

from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    """Manager para o CustomUser com e-mail como identificador principal."""

    def create_user(self, email: str, password: str = None, **extra_fields):
        if not email:
            raise ValueError("O campo e-mail é obrigatório.")
        email = self.normalize_email(email)
        extra_fields.setdefault("is_active", True)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "admin")

        if not extra_fields.get("is_staff"):
            raise ValueError("Superusuário deve ter is_staff=True.")
        if not extra_fields.get("is_superuser"):
            raise ValueError("Superusuário deve ter is_superuser=True.")

        return self.create_user(email, password, **extra_fields)
