from django.urls import path

from .views import RegisterView, EmailTokenObtainPairView


urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", EmailTokenObtainPairView.as_view(), name="email_token_obtain_pair"),
]


