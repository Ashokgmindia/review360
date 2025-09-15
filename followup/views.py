from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema_view, extend_schema

from .models import FollowUpSession
from .serializers import FollowUpSessionSerializer
from iam.mixins import CollegeScopedQuerysetMixin, IsAuthenticatedAndScoped, ActionRolePermission


@extend_schema_view(
    list=extend_schema(tags=["Follow-up"]),
    retrieve=extend_schema(tags=["Follow-up"]),
    create=extend_schema(tags=["Follow-up"]),
    update=extend_schema(tags=["Follow-up"]),
    partial_update=extend_schema(tags=["Follow-up"]),
    destroy=extend_schema(tags=["Follow-up"]),
)
class FollowUpSessionViewSet(CollegeScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = FollowUpSession.objects.select_related("college", "student", "activity_sheet", "teacher").order_by("-session_datetime")
    serializer_class = FollowUpSessionSerializer
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
    filterset_fields = ["status", "academic_year"]
    search_fields = ["student_name", "teacher_name", "objective", "location"]
    ordering_fields = ["session_datetime", "created_at"]


