from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema_view, extend_schema

from .models import Class, Student, ImportLog, Department, Subject, Teacher
from .serializers import (
    ClassSerializer,
    StudentSerializer,
    ImportLogSerializer,
    DepartmentSerializer,
    SubjectSerializer,
    TeacherSerializer,
)
from iam.mixins import CollegeScopedQuerysetMixin, IsAuthenticatedAndScoped, ActionRolePermission


@extend_schema_view(
    list=extend_schema(tags=["Academics"]),
    retrieve=extend_schema(tags=["Academics"]),
    create=extend_schema(tags=["Academics"]),
    update=extend_schema(tags=["Academics"]),
    partial_update=extend_schema(tags=["Academics"]),
    destroy=extend_schema(tags=["Academics"]),
)
class ClassViewSet(CollegeScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Class.objects.select_related("college", "teacher").order_by("name")
    serializer_class = ClassSerializer
    permission_classes = [IsAuthenticatedAndScoped, ActionRolePermission]
    role_perms = {
        "list": {"superadmin", "college_admin", "teacher"},
        "retrieve": {"superadmin", "college_admin", "teacher"},
        "create": {"superadmin", "college_admin"},
        "update": {"superadmin", "college_admin"},
        "partial_update": {"superadmin", "college_admin"},
        "destroy": {"superadmin", "college_admin"},
    }
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["academic_year", "is_active"]
    search_fields = ["name", "academic_year"]
    ordering_fields = ["name", "academic_year", "is_active"]

    def get_queryset(self):
        qs = super().get_queryset()
        request = getattr(self, "request", None)
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return qs.none()
        # Additional narrowing for teachers inside their college
        if getattr(user, "role", None) == "teacher":
            qs = qs.filter(teacher_id=user.id)
        return qs


@extend_schema_view(
    list=extend_schema(tags=["Academics"]),
    retrieve=extend_schema(tags=["Academics"]),
    create=extend_schema(tags=["Academics"]),
    update=extend_schema(tags=["Academics"]),
    partial_update=extend_schema(tags=["Academics"]),
    destroy=extend_schema(tags=["Academics"]),
)
class StudentViewSet(CollegeScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Student.objects.select_related("class_ref", "department", "college").order_by("last_name", "first_name")
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticatedAndScoped, ActionRolePermission]
    role_perms = {
        "list": {"superadmin", "college_admin", "teacher"},
        "retrieve": {"superadmin", "college_admin", "teacher"},
        "create": {"superadmin", "college_admin"},
        "update": {"superadmin", "college_admin"},
        "partial_update": {"superadmin", "college_admin"},
        "destroy": {"superadmin", "college_admin"},
    }
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["academic_year", "is_active", "class_ref"]
    search_fields = ["first_name", "last_name", "email"]
    ordering_fields = ["last_name", "first_name", "academic_year"]

    def get_queryset(self):
        qs = super().get_queryset()
        request = getattr(self, "request", None)
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return qs.none()
        if getattr(user, "role", None) == "teacher":
            qs = qs.filter(class_ref__teacher_id=user.id)
        return qs


@extend_schema_view(
    list=extend_schema(tags=["Academics"]),
    retrieve=extend_schema(tags=["Academics"]),
)
class ImportLogViewSet(CollegeScopedQuerysetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = ImportLog.objects.all().order_by("-imported_at")
    serializer_class = ImportLogSerializer
    permission_classes = [IsAuthenticatedAndScoped]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["class_ref"]
    ordering_fields = ["imported_at", "imported_count", "errors_count"]


@extend_schema_view(
    list=extend_schema(tags=["Academics"]),
    retrieve=extend_schema(tags=["Academics"]),
    create=extend_schema(tags=["Academics"]),
    update=extend_schema(tags=["Academics"]),
    partial_update=extend_schema(tags=["Academics"]),
    destroy=extend_schema(tags=["Academics"]),
)
class DepartmentViewSet(CollegeScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Department.objects.select_related("college", "hod").order_by("name")
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticatedAndScoped, ActionRolePermission]
    role_perms = {
        "list": {"superadmin", "college_admin", "teacher"},
        "retrieve": {"superadmin", "college_admin", "teacher"},
        "create": {"superadmin", "college_admin"},
        "update": {"superadmin", "college_admin"},
        "partial_update": {"superadmin", "college_admin"},
        "destroy": {"superadmin", "college_admin"},
    }
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "code"]
    ordering_fields = ["name", "code"]


@extend_schema_view(
    list=extend_schema(tags=["Academics"]),
    retrieve=extend_schema(tags=["Academics"]),
    create=extend_schema(tags=["Academics"]),
    update=extend_schema(tags=["Academics"]),
    partial_update=extend_schema(tags=["Academics"]),
    destroy=extend_schema(tags=["Academics"]),
)
class SubjectViewSet(CollegeScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Subject.objects.select_related("department", "college").order_by("name")
    serializer_class = SubjectSerializer
    permission_classes = [IsAuthenticatedAndScoped, ActionRolePermission]
    role_perms = {
        "list": {"superadmin", "college_admin", "teacher"},
        "retrieve": {"superadmin", "college_admin", "teacher"},
        "create": {"superadmin", "college_admin"},
        "update": {"superadmin", "college_admin"},
        "partial_update": {"superadmin", "college_admin"},
        "destroy": {"superadmin", "college_admin"},
    }
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "code"]
    ordering_fields = ["name", "code"]


@extend_schema_view(
    list=extend_schema(tags=["Academics"]),
    retrieve=extend_schema(tags=["Academics"]),
    create=extend_schema(tags=["Academics"]),
    update=extend_schema(tags=["Academics"]),
    partial_update=extend_schema(tags=["Academics"]),
    destroy=extend_schema(tags=["Academics"]),
)
class TeacherViewSet(CollegeScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Teacher.objects.select_related("user", "college", "department").prefetch_related("subjects_handled").order_by("last_name", "first_name")
    serializer_class = TeacherSerializer
    permission_classes = [IsAuthenticatedAndScoped, ActionRolePermission]
    role_perms = {
        "list": {"superadmin", "college_admin"},
        "retrieve": {"superadmin", "college_admin"},
        "create": {"superadmin", "college_admin"},
        "update": {"superadmin", "college_admin"},
        "partial_update": {"superadmin", "college_admin"},
        "destroy": {"superadmin", "college_admin"},
    }
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["department", "is_hod", "is_active"]
    search_fields = ["first_name", "last_name", "email", "employee_id"]
    ordering_fields = ["last_name", "first_name", "date_of_joining"]


