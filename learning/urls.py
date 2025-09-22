from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ActivitySheetViewSet, ValidationViewSet, SubjectViewSet, TopicViewSet


router = DefaultRouter()
router.register(r"activity-sheets", ActivitySheetViewSet, basename="activitysheet")
router.register(r"validations", ValidationViewSet, basename="validation")
router.register(r"subjects", SubjectViewSet, basename="subject")
router.register(r"topics", TopicViewSet, basename="topic")


# Learning module APIs with subjects and topics
urlpatterns = [
    path("", include(router.urls)),
]


