import random
import string

from django.urls import reverse
from rest_framework.test import APITestCase, APIClient

from user.test.factory import UserFactory
from user.models import User


class TestUser(object):
    def __init__(self, is_staff: bool = False):
        self.user_password = "".join(
            random.choices(string.ascii_letters + string.digits, k=8)
        )
        user = UserFactory.create(
            is_staff=is_staff,
            password=self.user_password,
            is_active=True,
        )
        self.user_id = user.id
        self._client_auth = APIClient()
        self._client_non_auth = APIClient()
        self._client_custom_auth = APIClient()
        self.set_auth_token(user.token)

    def set_auth_token(self, token: str):
        self._client_auth.credentials(HTTP_AUTHORIZATION="Token " + token)

    def set_custom_auth_token(self, token: str):
        self._client_custom_auth.credentials(HTTP_AUTHORIZATION="Token " + token)

    def get_user(self):
        return User.objects.get(pk=self.user_id)

    def get(self, url):
        return self._client_auth.get(url)

    def get_non_auth(self, url):
        return self._client_non_auth.get(url)

    def post(self, url, data=None):
        return self._client_auth.post(url, data)

    def post_non_auth(self, url, data=None):
        return self._client_non_auth.post(url, data)

    def post_custom_auth(self, url, data=None):
        return self._client_custom_auth.post(url, data)

    def put(self, url, data):
        return self._client_auth.put(url, data)

    def put_non_auth(self, url, data):
        return self._client_non_auth.put(url, data)

    def delete(self, url, data):
        return self._client_auth.delete(url, data)

    def delete_non_auth(self, url, data):
        return self._client_non_auth.delete(url, data)


class BaseAPITestCase(APITestCase):
    url: str
    api_detail: str
    default_pk: int or str
    user: TestUser
    admin: TestUser
    request_user: TestUser
    tested_user: TestUser

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = TestUser()
        cls.admin = TestUser(is_staff=True)

    def get_detail_url(self, pk=None):
        return reverse(self.api_detail, kwargs={"pk": pk if pk else self.default_pk})
