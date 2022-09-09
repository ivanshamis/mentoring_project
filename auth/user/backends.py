import jwt
import re

from django.conf import settings
from django.contrib.auth.backends import ModelBackend
from django.core.cache import cache

from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed

from user.constants import ErrorMessages, MIN_PASSWORD_LENGTH
from user.models import User


class CustomModelBackend(ModelBackend):
    def user_can_authenticate(self, user):
        return True


class JWTAuthentication(authentication.BaseAuthentication):
    authentication_header_prefix = "Token"

    def authenticate(self, request):
        request.user = None
        auth_header = authentication.get_authorization_header(request).split()
        auth_header_prefix = self.authentication_header_prefix.lower()

        if not auth_header:
            return None

        if len(auth_header) != 2:
            return None

        prefix = auth_header[0].decode("utf-8")
        token = auth_header[1].decode("utf-8")

        if prefix.lower() != auth_header_prefix:
            return None

        return self._authenticate_credentials(request, token)

    def _authenticate_credentials(self, request, token):
        user, token = validate_token(token, action="login")

        if not user.is_active:
            raise AuthenticationFailed(ErrorMessages.USER_IS_DEACTIVATED)

        return user, token


def decode_token(token: str):
    return jwt.decode(token, settings.PUBLIC_KEY, algorithms="RS256")


def get_payload_user(payload: dict):
    return User.objects.get(pk=payload["id"])


def validate_token(token: str, action: str, invalidate: bool = False):
    if cache.get(token):
        raise AuthenticationFailed(ErrorMessages.INVALID_TOKEN)

    try:
        payload = decode_token(token)
    except Exception:
        raise AuthenticationFailed(ErrorMessages.INVALID_TOKEN)

    if payload.get("action") != action:
        raise AuthenticationFailed(ErrorMessages.INVALID_TOKEN_ACTION)

    try:
        user = get_payload_user(payload)
    except User.DoesNotExist:
        raise AuthenticationFailed(ErrorMessages.INVALID_TOKEN_USER)

    if invalidate:
        cache.set(token, user.pk, settings.TOKEN_EXPIRES[action])

    return user, token


def validate_password(p: str) -> bool:
    lower_chars = '(?=.*?[a-z])'
    UPPER_CHARS = '(?=.*?[A-Z])'
    DIGITS = '(?=.*?[0-9])'
    SPECIAL_CHARS = '(?=.*?[#?!@$%^&*-])'
    LENGTH = '{' + str(MIN_PASSWORD_LENGTH) + ',}'
    PASSWORD_PATTERN = f'^{UPPER_CHARS}{lower_chars}{DIGITS}{SPECIAL_CHARS}.{LENGTH}$'

    password_pattern = re.compile(PASSWORD_PATTERN)

    return bool(password_pattern.match(p))
