from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema_view, extend_schema

from .models import FollowUpSession
from .serializers import FollowUpSessionSerializer
from iam.mixins import CollegeScopedQuerysetMixin, IsAuthenticatedAndScoped, ActionRolePermission
from iam.permissions import RoleBasedPermission, FieldLevelPermission, TenantScopedPermission


@extend_schema_view(
    list=extend_schema(tags=["Followup"]),
    retrieve=extend_schema(tags=["Followup"]),
    create=extend_schema(tags=["Followup"]),
    update=extend_schema(tags=["Followup"]),
    partial_update=extend_schema(tags=["Followup"]),
    destroy=extend_schema(tags=["Followup"]),
)
class FollowUpSessionViewSet(CollegeScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = FollowUpSession.objects.select_related("college", "student", "subject", "topic", "teacher").order_by("-session_datetime")
    serializer_class = FollowUpSessionSerializer
    permission_classes = [IsAuthenticatedAndScoped, RoleBasedPermission, TenantScopedPermission, FieldLevelPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "academic_year"]
    search_fields = ["student_name", "teacher_name", "objective", "location"]
    ordering_fields = ["session_datetime", "created_at"]


