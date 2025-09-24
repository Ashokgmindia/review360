from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FollowUpSessionViewSet


router = DefaultRouter()
router.register(r"sessions", FollowUpSessionViewSet, basename="followup-sessions")


urlpatterns = [
    path("", include(router.urls)),
]


