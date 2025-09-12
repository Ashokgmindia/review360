from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClassViewSet, StudentViewSet, ImportLogViewSet


router = DefaultRouter()
router.register(r"classes", ClassViewSet, basename="class")
router.register(r"students", StudentViewSet, basename="student")
router.register(r"import-logs", ImportLogViewSet, basename="importlog")


urlpatterns = [
    path("", include(router.urls)),
]


