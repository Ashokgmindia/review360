from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ActivitySheetViewSet, ValidationViewSet


router = DefaultRouter()
router.register(r"activity-sheets", ActivitySheetViewSet, basename="activitysheet")
router.register(r"validations", ValidationViewSet, basename="validation")


urlpatterns = [
    path("", include(router.urls)),
]


