from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


urlpatterns = [
    path("review360/backend/", include([
        path("admin/", admin.site.urls),
        # JWT Token endpoints
        path("api/v1/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
        path("api/v1/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
        # IAM module (auth, token, colleges)
        path("api/v1/iam/", include("iam.urls")),
        path("api/v1/academics/", include("academics.urls")),
        path("api/v1/learning/", include("learning.urls")),
        path("api/v1/followup/", include("followup.urls")),
        path("api/v1/compliance/", include("compliance.urls")),
        # API schema and documentation
        path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
        path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
        path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    ])),
]


