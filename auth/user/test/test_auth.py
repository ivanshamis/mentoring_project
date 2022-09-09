import time
import uuid
from unittest.mock import patch

from django.test import override_settings
from django.urls import reverse
from rest_framework import status

from user.test.factory import UserFactory
from user.test.test_user import API_DETAIL
from user.test.utils import BaseAPITestCase
from user.constants import ErrorMessages, MIN_PASSWORD_LENGTH
from user.models import User, generate_token_by_pk

API_AUTH = "api:auth"


class UserSignupTestCase(BaseAPITestCase):
    url = reverse(API_AUTH + "-signup")

    def test_signup(self):
        new_user = UserFactory.build()
        response = self.user.post_non_auth(
            self.url,
            data={
                "email": new_user.email,
                "username": new_user.username,
                "password": new_user.password,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.data, {"email": new_user.email, "username": new_user.username}
        )
        user = User.objects.filter(email=new_user.email, username=new_user.username)
        self.assertTrue(user.exists())
        self.assertTrue(not user.get().is_active)

    def test_signup_send_email(self):
        new_user = UserFactory.build()
        with patch("user.message_sender.EmailSender._send_email") as mock:
            self.user.post_non_auth(
                self.url,
                data={
                    "email": new_user.email,
                    "username": new_user.username,
                    "password": new_user.password,
                },
            )
            mock.assert_called_with(
                email=new_user.email,
                message=new_user.get_email_message("ACTIVATE_ACCOUNT"),
            )

    def test_signup_exists(self):
        existing_user = self.user.get_user()
        response = self.user.post_non_auth(
            self.url,
            data={
                "email": existing_user.email,
                "username": existing_user.username,
                "password": existing_user.password,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        for field in ["email", "username"]:
            self.assertEqual(
                response.data.get("errors").get(field)[0],
                ErrorMessages.USER_FIELD_EXISTS.format(field=field),
            )

    def test_signup_no_email(self):
        new_user = UserFactory.build()
        response = self.user.post_non_auth(
            self.url,
            data={"username": new_user.username, "password": new_user.password},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data.get("errors").get("email")[0], ErrorMessages.FIELD_IS_REQUIRED
        )

    def test_signup_wrong_email(self):
        new_user = UserFactory.build()
        response = self.user.post_non_auth(
            self.url,
            data={
                "email": new_user.username,
                "username": new_user.username,
                "password": new_user.password,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data.get("errors").get("email")[0], ErrorMessages.NOT_VALID_EMAIL
        )

    def test_signup_no_password(self):
        new_user = UserFactory.build()
        response = self.user.post_non_auth(
            self.url,
            data={"email": new_user.email, "username": new_user.username},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data.get("errors").get("password")[0],
            ErrorMessages.FIELD_IS_REQUIRED,
        )

    def test_signup_no_username(self):
        new_user = UserFactory.build()
        response = self.user.post_non_auth(
            self.url,
            data={"email": new_user.email, "password": new_user.password},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data.get("errors").get("username")[0],
            ErrorMessages.FIELD_IS_REQUIRED,
        )

    def test_signup_weak_password(self):
        new_user = UserFactory.build()
        response = self.user.post_non_auth(
            self.url,
            data={
                "email": new_user.email,
                "username": new_user.username,
                "password": "1" * (MIN_PASSWORD_LENGTH - 1),
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data.get("errors").get("password")[0],
            ErrorMessages.WEAK_PASSWORD.format(min_length=MIN_PASSWORD_LENGTH),
        )


class UserLoginTestCase(BaseAPITestCase):
    url = reverse(API_AUTH + "-login")

    def test_login(self):
        existing_user = self.user.get_user()
        existing_password = self.user.user_password
        response = self.user.post_non_auth(
            self.url,
            data={"username": existing_user.email, "password": existing_password},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue("token" in response.data)

    def test_inactive(self):
        existing_password = self.user.user_password
        user = UserFactory.create(is_active=False, password=existing_password)
        response = self.user.post_non_auth(
            self.url,
            data={"username": user.email, "password": existing_password},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIsInstance(response.data.get("errors"), list)
        self.assertEqual(
            response.data.get("errors")[0], ErrorMessages.USER_IS_DEACTIVATED
        )

    def test_wrong_password(self):
        user = self.user.get_user()
        user_password = self.user.user_password
        response = self.user.post_non_auth(
            self.url,
            data={"username": user.email, "password": user_password + "_wrong"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIsInstance(response.data.get("errors"), list)
        self.assertEqual(
            response.data.get("errors")[0], ErrorMessages.USER_WRONG_CREDENTIALS
        )


class UserLogoutTestCase(BaseAPITestCase):
    url = reverse(API_AUTH + "-logout")

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.api_detail = API_DETAIL
        cls.default_pk = "me"

    def test_logout(self):
        response = self.user.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        response = self.user.get(self.get_detail_url("me"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data.get("detail"), ErrorMessages.INVALID_TOKEN)

    def test_logout_non_auth(self):
        response = self.user.post_non_auth(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data.get("detail"), ErrorMessages.INVALID_TOKEN)

    def test_logout_invalid_token_action(self):
        existing_user = self.user.get_user()
        self.user.set_custom_auth_token(existing_user.generate_token("activate"))
        response = self.user.post_custom_auth(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data.get("detail"), ErrorMessages.INVALID_TOKEN_ACTION
        )

    def test_invalid_token_user(self):
        self.user.set_custom_auth_token(
            generate_token_by_pk(action="login", pk=uuid.uuid4())
        )
        response = self.user.post_custom_auth(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data.get("detail"), ErrorMessages.INVALID_TOKEN_USER)


class UserResetPasswordTestCase(BaseAPITestCase):
    url = reverse(API_AUTH + "-password-reset")

    def test_reset_password(self):
        existing_user = self.user.get_user()
        with patch("user.message_sender.EmailSender._send_email") as mock:
            response = self.user.post_non_auth(
                self.url, data={"username": existing_user.username}
            )
            self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
            mock.assert_called_with(
                email=existing_user.email,
                message=existing_user.get_email_message("PASSWORD_RESET"),
            )

    def test_reset_user_not_found(self):
        existing_user = self.user.get_user()
        response = self.user.post_non_auth(
            self.url, data={"username": existing_user.username + "_wrong"}
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class UserSetupPasswordTestCase(BaseAPITestCase):
    url = reverse(API_AUTH + "-password-setup")
    url_login = reverse(API_AUTH + "-login")
    new_password = "newP@ssw0rd"

    def test_setup_password(self):
        existing_user = self.user.get_user()
        token = existing_user.generate_token("password")
        response = self.user.post_non_auth(
            self.url, data={"token": token, "password": self.new_password}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data.get("username"), existing_user.username)

        response = self.user.post_non_auth(
            self.url_login,
            data={"username": existing_user.email, "password": self.new_password},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue("token" in response.data)

    def test_setup_password_no_password(self):
        existing_user = self.user.get_user()
        token = existing_user.generate_token("password")
        response = self.user.post_non_auth(self.url, data={"token": token})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data.get("errors").get("password")[0],
            ErrorMessages.FIELD_IS_REQUIRED,
        )

    def test_setup_weak_password(self):
        existing_user = self.user.get_user()
        token = existing_user.generate_token("password")
        response = self.user.post_non_auth(
            self.url, data={"token": token, "password": "1" * (MIN_PASSWORD_LENGTH - 1)}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data.get("errors").get("password")[0],
            ErrorMessages.WEAK_PASSWORD.format(min_length=MIN_PASSWORD_LENGTH),
        )

    def test_setup_password_no_token(self):
        response = self.user.post_non_auth(
            self.url, data={"password": self.new_password}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data.get("errors").get("token")[0], ErrorMessages.FIELD_IS_REQUIRED
        )

    def test_setup_password_invalid_token_user(self):
        token = generate_token_by_pk(action="password", pk=uuid.uuid4())
        response = self.user.post_non_auth(
            self.url, data={"token": token, "password": self.new_password}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data.get("detail"), ErrorMessages.INVALID_TOKEN_USER)

    def test_setup_password_invalid_token_action(self):
        existing_user = self.user.get_user()
        token = existing_user.generate_token("login")
        response = self.user.post_non_auth(
            self.url, data={"token": token, "password": self.new_password}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data.get("detail"), ErrorMessages.INVALID_TOKEN_ACTION
        )

    def test_setup_password_invalid_token(self):
        token = "xxx-xxx-xxx-xxx"
        response = self.user.post_non_auth(
            self.url, data={"token": token, "password": self.new_password}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data.get("detail"), ErrorMessages.INVALID_TOKEN)

    @override_settings(TOKEN_EXPIRES={"password": 1})
    def test_setup_password_token_expired(self):
        existing_user = self.user.get_user()
        token = existing_user.generate_token("password")
        time.sleep(2)
        response = self.user.post_non_auth(
            self.url, data={"token": token, "password": self.new_password}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data.get("detail"), ErrorMessages.INVALID_TOKEN)

    def test_setup_password_token_is_used(self):
        existing_user = self.user.get_user()
        token = existing_user.generate_token("password")
        data = {"token": token, "password": self.new_password}
        self.user.post_non_auth(self.url, data=data)
        response = self.user.post_non_auth(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data.get("detail"), ErrorMessages.INVALID_TOKEN)
