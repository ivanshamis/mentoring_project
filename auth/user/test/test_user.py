import time
import uuid

from django.test import override_settings
from rest_framework import status

from ..constants import ErrorMessages, MIN_PASSWORD_LENGTH
from .utils import BaseAPITestCase
from ..models import generate_token_by_pk

API_DETAIL = "api:user-detail"
API_CHANGE_PASSWORD = "api:user-change-password"


class UserGetTestCase(BaseAPITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.request_user = cls.user
        cls.tested_user = cls.admin
        cls.api_detail = API_DETAIL
        cls.default_pk = cls.tested_user.user_id

    def test_get(self):
        response = self.request_user.get(self.get_detail_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for field in ["id", "email", "username", "first_name", "last_name"]:
            self.assertEqual(
                response.data.get(field),
                str(getattr(self.tested_user.get_user(), field)),
            )

    def test_get_non_auth(self):
        response = self.request_user.get_non_auth(self.get_detail_url())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data.get("detail"), ErrorMessages.NOT_AUTHENTICATED)

    def test_get_not_exists(self):
        response = self.request_user.get(self.get_detail_url(1_000_000))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data.get("detail"), ErrorMessages.NOT_FOUND)

    def test_get_bad_pk(self):
        response = self.request_user.get(self.get_detail_url("some_string"))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data.get("detail"), ErrorMessages.NOT_FOUND)


class UserUpdateTestCase(BaseAPITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.api_detail = API_DETAIL
        cls.default_pk = cls.admin.user_id

    def test_update_not_allowed(self):
        response = self.user.put(
            self.get_detail_url(), data={"username": "new_username"}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data.get("error"), ErrorMessages.NOT_ALLOWED)


class UserGetCurrentTestCase(BaseAPITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.api_detail = API_DETAIL
        cls.default_pk = "me"

    def test_get_me(self):
        response = self.user.get(self.get_detail_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_me_non_auth(self):
        response = self.user.get_non_auth(self.get_detail_url())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data.get("detail"), ErrorMessages.NOT_AUTHENTICATED)

    @override_settings(TOKEN_EXPIRES={"login": 1})
    def test_get_me_login_expired(self):
        self.user.set_auth_token(self.user.get_user().token)
        time.sleep(1)
        response = self.user.get(self.get_detail_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        time.sleep(2)
        response = self.user.get(self.get_detail_url())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data.get("detail"), ErrorMessages.INVALID_TOKEN)

    def test_get_me_invalid_token(self):
        self.user.set_auth_token("xxx-xxx-xxx")
        response = self.user.get(self.get_detail_url())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data.get("detail"), ErrorMessages.INVALID_TOKEN)

    def test_get_me_invalid_token_action(self):
        token = self.user.get_user().generate_token("password")
        self.user.set_auth_token(token)
        response = self.user.get(self.get_detail_url())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data.get("detail"), ErrorMessages.INVALID_TOKEN_ACTION
        )

    def test_get_me_invalid_token_user(self):
        token = generate_token_by_pk(action="login", pk=uuid.uuid4())
        self.user.set_auth_token(token)
        response = self.user.get(self.get_detail_url())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data.get("detail"), ErrorMessages.INVALID_TOKEN_USER)


class UserUpdateCurrentTestCase(BaseAPITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.api_detail = API_DETAIL
        cls.default_pk = "me"

    def test_update_me(self):
        new_username = "new_username"
        response = self.user.put(self.get_detail_url(), data={"username": new_username})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.get_user().username, new_username)

    def test_update_me_non_auth(self):
        response = self.user.put_non_auth(
            self.get_detail_url(), data={"username": "username"}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data.get("detail"), ErrorMessages.NOT_AUTHENTICATED)

    def test_update_me_no_username(self):
        response = self.user.put(
            self.get_detail_url(), data={"first_name": "first_name"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data.get("errors").get("username")[0],
            ErrorMessages.FIELD_IS_REQUIRED,
        )

    def test_update_me_readonly_email(self):
        old_email = self.user.get_user().email
        response = self.user.put(
            self.get_detail_url(),
            data={"username": "new_username", "email": "new@emai.com"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.get_user().email, old_email)

    def test_update_me_readonly_is_active(self):
        old_is_active = self.user.get_user().is_active
        response = self.user.put(
            self.get_detail_url(),
            data={"username": "new_username", "is_active": not old_is_active},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.get_user().is_active, old_is_active)

    def test_update_me_readonly_is_staff(self):
        old_is_staff = self.user.get_user().is_staff
        response = self.user.put(
            self.get_detail_url(),
            data={"username": "new_username", "is_staff": not old_is_staff},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.get_user().is_staff, old_is_staff)


class UserChangePasswordTestCase(BaseAPITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.api_detail = API_CHANGE_PASSWORD
        cls.default_pk = "me"
        new_password = "P@ssw0rd"
        cls.valid_data = {
            "old_password": cls.user.user_password,
            "password": new_password,
            "password_repeat": new_password,
        }

    def test_change_password(self):
        data = dict(self.valid_data)
        response = self.user.post(self.get_detail_url(), data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("username"), self.user.get_user().username)
        self.assertTrue(self.user.get_user().check_password(data["password"]))

    def test_change_password_wrong_old(self):
        data = dict(self.valid_data)
        data["old_password"] += "_wrong"
        response = self.user.post(self.get_detail_url(), data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data.get("errors")[0],
            ErrorMessages.PASSWORD_IS_WRONG,
        )

    def test_change_password_wrong_repeat(self):
        data = dict(self.valid_data)
        data["password_repeat"] += "_wrong"
        response = self.user.post(self.get_detail_url(), data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data.get("errors").get("error")[0],
            ErrorMessages.PASSWORD_NO_MATCH,
        )

    def test_change_password_non_auth(self):
        data = dict(self.valid_data)
        response = self.user.post_non_auth(self.get_detail_url(), data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data.get("detail"), ErrorMessages.NOT_AUTHENTICATED)

    def test_change_password_not_me(self):
        data = dict(self.valid_data)
        response = self.user.post(self.get_detail_url(pk=self.user.user_id), data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data.get("error"), ErrorMessages.NOT_ALLOWED)

    @staticmethod
    def change_data_password(data, password):
        data.update({"password": password, "password_repeat": password})
        return data

    def test_change_password_weak(self):
        data = dict(self.valid_data)
        weak_password = "1" * (MIN_PASSWORD_LENGTH - 1)
        data = self.change_data_password(data, weak_password)
        response = self.user.post(self.get_detail_url(), data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        for field in ["password", "password_repeat"]:
            self.assertEqual(
                response.data.get("errors").get(field)[0],
                ErrorMessages.WEAK_PASSWORD.format(min_length=MIN_PASSWORD_LENGTH),
            )

    def test_change_password_weak_no_digits(self):
        data = dict(self.valid_data)
        data = self.change_data_password(data, "P@ssword")
        response = self.user.post(self.get_detail_url(), data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data.get("errors").get("error")[0],
            ErrorMessages.WEAK_PASSWORD_SPEC,
        )

    def test_change_password_weak_no_upper(self):
        data = dict(self.valid_data)
        data = self.change_data_password(data, "p@ssword")
        response = self.user.post(self.get_detail_url(), data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data.get("errors").get("error")[0],
            ErrorMessages.WEAK_PASSWORD_SPEC,
        )

    def test_change_password_weak_no_spec(self):
        data = dict(self.valid_data)
        data = self.change_data_password(data, "Passw0rd")
        response = self.user.post(self.get_detail_url(), data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data.get("errors").get("error")[0],
            ErrorMessages.WEAK_PASSWORD_SPEC,
        )
