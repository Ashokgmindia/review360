from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterView, LoginView, OTPVerifyView, CollegeViewSet, 
    IamTokenObtainPairView, IamTokenRefreshView, MeView,
    PasswordResetRequestView, PasswordResetConfirmView, LogoutView
)

router = DefaultRouter()
router.register(r"colleges", CollegeViewSet, basename="college")

urlpatterns = [
    # path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/otp-verify/", OTPVerifyView.as_view(), name="otp_verify"),
    path("auth/password-reset-request/", PasswordResetRequestView.as_view(), name="password_reset_request"),
    path("auth/password-reset-confirm/", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("token/", IamTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", IamTokenRefreshView.as_view(), name="token_refresh"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
    path("", include(router.urls)),
]