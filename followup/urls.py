from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FollowUpSessionViewSet, LocationViewSet, ObjectiveViewSet, schedule_session_view


router = DefaultRouter()
router.register(r"sessions", FollowUpSessionViewSet, basename="followup-sessions")
router.register(r"locations", LocationViewSet, basename="followup-locations")
router.register(r"objectives", ObjectiveViewSet, basename="followup-objectives")


urlpatterns = [
    path("", include(router.urls)),
    path("schedule/", schedule_session_view, name="schedule_session"),
]


