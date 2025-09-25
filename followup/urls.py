from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FollowUpSessionViewSet, schedule_session_view


router = DefaultRouter()
router.register(r"sessions", FollowUpSessionViewSet, basename="followup-sessions")


urlpatterns = [
    path("", include(router.urls)),
    path("schedule/", schedule_session_view, name="schedule_session"),
]


