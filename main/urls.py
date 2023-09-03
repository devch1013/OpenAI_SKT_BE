from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="OpenAI X SKT 프로젝트",
        default_version="1.0.0",
        description="OpenAI X SKT 프로젝트 API 문서",
        terms_of_service="",
    ),
    public=True,
    permission_classes=[],
    authentication_classes=[],
)


urlpatterns = [
    path(r"swagger", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path(
        r"swagger(?P<format>\.json|\.yaml)",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
    path(r"redoc", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc-v1"),
    path("admin/", admin.site.urls),
    path("api/user/", include("users.urls")),
    path("api/project/", include("drafts.urls")),
]
