from django.urls import reverse
from rest_framework import status

from .test_user import UserGetTestCase
from .utils import BaseAPITestCase
from ..constants import ErrorMessages
from ..models import User

API_ADMIN = "api:admin"


class AdminListingTestCase(BaseAPITestCase):
    url = reverse(API_ADMIN + "-list")

    def test_listing(self):
        response = self.admin.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data.get("results"), list)
        self.assertEqual(len(response.data.get("results")), User.objects.count())

    def test_listing_non_auth(self):
        response = self.admin.get_non_auth(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data.get("detail"), ErrorMessages.NOT_AUTHENTICATED)

    def test_listing_non_admin(self):
        response = self.user.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data.get("detail"), ErrorMessages.NO_PERMISSION)


class AdminGetTestCase(UserGetTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.request_user = cls.admin
        cls.tested_user = cls.user
        cls.api_detail = API_ADMIN + "-detail"
        cls.default_pk = cls.tested_user.user_id


class AdminUpdateTestCase(BaseAPITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.api_detail = API_ADMIN + "-detail"
        cls.default_pk = cls.user.user_id

    def test_update(self):
        new_username = "new_username_from_admin"
        response = self.admin.put(
            self.get_detail_url(), data={"username": new_username}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.get_user().username, new_username)

    def test_update_non_auth(self):
        response = self.admin.put_non_auth(
            self.get_detail_url(), data={"username": "username"}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data.get("detail"), ErrorMessages.NOT_AUTHENTICATED)

    def test_update_non_admin(self):
        response = self.user.put(self.get_detail_url(), data={"username": "username"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data.get("detail"), ErrorMessages.NO_PERMISSION)
