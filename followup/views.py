from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend

from .models import FollowUpSession
from .serializers import FollowUpSessionSerializer


class FollowUpSessionViewSet(viewsets.ModelViewSet):
    queryset = FollowUpSession.objects.all().order_by("-session_datetime")
    serializer_class = FollowUpSessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "academic_year"]
    search_fields = ["student_name", "teacher_name", "objective", "location"]
    ordering_fields = ["session_datetime", "created_at"]


