from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RegisterView, EmailTokenObtainPairView, CollegeViewSet, IamTokenObtainPairView, IamTokenRefreshView, MeView


router = DefaultRouter()
router.register(r"colleges", CollegeViewSet, basename="college")


urlpatterns = [
    # path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", EmailTokenObtainPairView.as_view(), name="email_token_obtain_pair"),
    path("token/", IamTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", IamTokenRefreshView.as_view(), name="token_refresh"),
    path("me/", MeView.as_view(), name="me"),
    path("", include(router.urls)),
]


