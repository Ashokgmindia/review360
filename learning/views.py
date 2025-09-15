from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema_view, extend_schema

from .models import ActivitySheet, Validation
from .serializers import ActivitySheetSerializer, ValidationSerializer
from iam.mixins import CollegeScopedQuerysetMixin, IsAuthenticatedAndScoped, ActionRolePermission


@extend_schema_view(
    list=extend_schema(tags=["Learning"]),
    retrieve=extend_schema(tags=["Learning"]),
    create=extend_schema(tags=["Learning"]),
    update=extend_schema(tags=["Learning"]),
    partial_update=extend_schema(tags=["Learning"]),
    destroy=extend_schema(tags=["Learning"]),
)
class ActivitySheetViewSet(CollegeScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = ActivitySheet.objects.select_related("college", "student").order_by("-created_at")
    serializer_class = ActivitySheetSerializer
    permission_classes = [IsAuthenticatedAndScoped, ActionRolePermission]
    role_perms = {
        "list": {"superadmin", "college_admin", "teacher"},
        "retrieve": {"superadmin", "college_admin", "teacher"},
        "create": {"superadmin", "college_admin", "teacher"},
        "update": {"superadmin", "college_admin", "teacher"},
        "partial_update": {"superadmin", "college_admin", "teacher"},
        "destroy": {"superadmin", "college_admin"},
    }
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["sheet_type", "status", "academic_year"]
    search_fields = ["student_name", "title", "context", "objectives", "methodology"]
    ordering_fields = ["created_at", "updated_at", "final_grade"]


@extend_schema_view(
    list=extend_schema(tags=["Learning"]),
    retrieve=extend_schema(tags=["Learning"]),
    create=extend_schema(tags=["Learning"]),
    update=extend_schema(tags=["Learning"]),
    partial_update=extend_schema(tags=["Learning"]),
    destroy=extend_schema(tags=["Learning"]),
)
class ValidationViewSet(CollegeScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Validation.objects.select_related("college", "activity_sheet", "teacher").order_by("-validation_date")
    serializer_class = ValidationSerializer
    permission_classes = [IsAuthenticatedAndScoped, ActionRolePermission]
    role_perms = {
        "list": {"superadmin", "college_admin", "teacher"},
        "retrieve": {"superadmin", "college_admin", "teacher"},
        "create": {"superadmin", "college_admin", "teacher"},
        "update": {"superadmin", "college_admin", "teacher"},
        "partial_update": {"superadmin", "college_admin", "teacher"},
        "destroy": {"superadmin", "college_admin"},
    }
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["activity_sheet"]
    ordering_fields = ["validation_date", "session_grade"]


