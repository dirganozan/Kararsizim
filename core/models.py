from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model for Krarsızım.
    Ensures email is unique and required.
    """
    email = models.EmailField(
        'E-posta Adresi',
        unique=True,
        blank=False,
        error_messages={
            'unique': 'Bu e-posta adresi ile zaten kayıtlı bir hesap var.',
        }
    )

    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return f"@{self.username}"
