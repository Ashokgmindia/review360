from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ClassViewSet,
    StudentViewSet,
    ImportLogViewSet,
    DepartmentViewSet,
    SubjectViewSet,
    TeacherViewSet,
)


router = DefaultRouter()
router.register(r"classes", ClassViewSet, basename="class")
router.register(r"students", StudentViewSet, basename="student")
router.register(r"import-logs", ImportLogViewSet, basename="importlog")
router.register(r"departments", DepartmentViewSet, basename="department")
router.register(r"subjects", SubjectViewSet, basename="subject")
router.register(r"teachers", TeacherViewSet, basename="teacher")


urlpatterns = [
    path("", include(router.urls)),
]


