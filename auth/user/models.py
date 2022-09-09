import uuid

import jwt

from datetime import datetime, timedelta

from django.dispatch import receiver
from django.db.models.signals import post_save
from django.conf import settings
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)

from django.db import models
from django.urls import reverse

from user.constants import ErrorMessages, EmailTemplates
from user.message_sender import email_sender


class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None):
        if username is None:
            raise TypeError(ErrorMessages.USER_MUST_HAVE_USERNAME)

        if email is None:
            raise TypeError(ErrorMessages.USER_MUST_HAVE_EMAIL)

        user = self.model(username=username, email=self.normalize_email(email))
        user.set_password(password)
        user.save()

        return user

    def create_superuser(self, username, email, password):
        if password is None:
            raise TypeError(ErrorMessages.SUPERUSER_MUST_HAVE_PASSWORD)

        user = self.create_user(username, email, password)
        user.is_superuser = True
        user.is_staff = True
        user.save()

        return user


def generate_token_by_pk(action: str, pk: uuid.UUID):
    dt = datetime.now() + timedelta(seconds=settings.TOKEN_EXPIRES[action])

    token = jwt.encode(
        {
            "id": str(pk),
            "action": action,
            "exp": int(dt.strftime("%s")),
        },
        settings.PRIVATE_KEY,
        algorithm="RS256",
    )

    return token


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(db_index=True, max_length=255, unique=True)
    email = models.EmailField(db_index=True, unique=True)
    first_name = models.CharField(max_length=100, null=True, blank=False)
    last_name = models.CharField(max_length=100, null=True, blank=False)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    objects = UserManager()

    def __str__(self):
        return self.email

    @property
    def token(self):
        return self.generate_token(action="login")

    def get_url(self, action: str, path: str):
        token = self.generate_token(action=action)
        return f"{settings.SITE_URL}{reverse(path)}?token={token}"

    def get_activate_url(self):
        return self.get_url(action="activate", path="api:auth-activate")

    def get_password_url(self):
        return self.get_url(action="password", path="api:auth-password-setup")

    def get_email_message(self, template: str):
        action = template.split("_")[0].lower()
        get_action_url = getattr(self, f"get_{action}_url")
        message = EmailTemplates.templates[template]
        message.body = message.body.format(url=get_action_url())
        return message

    def get_full_name(self):
        return self.username

    def get_short_name(self):
        return self.username

    def generate_token(self, action: str):
        return generate_token_by_pk(action=action, pk=self.pk)


@receiver(post_save, sender=User)
def save_profile(sender, instance, created, **kwargs):
    if created:
        email_sender.send_message(
            instance, instance.get_email_message("ACTIVATE_ACCOUNT")
        )
