from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ClassViewSet,
    StudentViewSet,
    ImportLogViewSet,
    DepartmentViewSet,
    SubjectViewSet,
    TeacherViewSet,
    TopicViewSet,
)
from .bulk_upload_views import bulk_upload_teacher_users, bulk_upload_student_users


router = DefaultRouter()
router.register(r"classes", ClassViewSet, basename="class")
router.register(r"students", StudentViewSet, basename="student")
router.register(r"import-logs", ImportLogViewSet, basename="importlog")
router.register(r"departments", DepartmentViewSet, basename="department")
router.register(r"subjects", SubjectViewSet, basename="subject")
router.register(r"teachers", TeacherViewSet, basename="teacher")
router.register(r"topics", TopicViewSet, basename="topic")


urlpatterns = [
    path("", include(router.urls)),
    # Separate bulk upload endpoints for User accounts only
    path("bulk-upload/teacher-users/", bulk_upload_teacher_users, name="bulk-upload-teacher-users"),
    path("bulk-upload/student-users/", bulk_upload_student_users, name="bulk-upload-student-users"),
]


