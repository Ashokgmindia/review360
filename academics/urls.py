from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ClassViewSet,
    StudentViewSet,
    DepartmentViewSet,
    TeacherViewSet,
    StudentSubjectsUpdateViewSet,
)
from .bulk_upload_views import bulk_upload_teacher_users


router = DefaultRouter()
router.register(r"classes", ClassViewSet, basename="class")
router.register(r"students", StudentViewSet, basename="student")
router.register(r"departments", DepartmentViewSet, basename="department")
router.register(r"teachers", TeacherViewSet, basename="teacher")


urlpatterns = [
    path("", include(router.urls)),
    # Bulk upload endpoints
    path("bulk-upload/teachers/", bulk_upload_teacher_users, name="bulk-upload-teachers"),
    # Student subjects update endpoint
    path(
        "students/class/<int:class_id>/student/<int:student_id>/subjects/",
        StudentSubjectsUpdateViewSet.as_view({'put': 'update', 'patch': 'update'}),
        name="student-subjects-update"
    ),
]


