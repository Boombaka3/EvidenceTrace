# llm_eval_harness/apps/users/models.py
import secrets

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model in the PUBLIC schema. Extends AbstractUser to keep all
    standard Django auth behaviour while giving us room to add tenant-scoped
    profile fields later without a migration on the built-in User table.
    """
    email = models.EmailField(unique=True)
    api_key = models.CharField(max_length=64, unique=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        app_label = "users"

    def save(self, *args, **kwargs):
        if not self.api_key:
            self.api_key = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)
