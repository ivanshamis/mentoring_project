from django.contrib import admin
from django.urls import path, include
from rest_framework.documentation import include_docs_urls
from rest_framework.permissions import AllowAny
from rest_framework.routers import SimpleRouter

from user.views import AuthViewSet, UserViewSet, AdminUserViewSet

router = SimpleRouter()
router.register("auth", AuthViewSet, basename="auth")
router.register("users", UserViewSet, basename="user")
router.register("admin/users", AdminUserViewSet, basename="admin")

api_urls = [path("api/", include((router.urls, "api"), namespace="api"))]

urlpatterns = [
    path("admin/", admin.site.urls),
    *api_urls,
    path(
        "docs/",
        include_docs_urls(
            title="API", patterns=api_urls, permission_classes=[AllowAny]
        ),
    ),
]
