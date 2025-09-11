from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import College
from .serializers import CollegeSerializer


class CollegeViewSet(viewsets.ModelViewSet):
    queryset = College.objects.all().order_by("name")
    serializer_class = CollegeSerializer
    permission_classes = [permissions.IsAuthenticated]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["is_active", "code"]
    search_fields = ["name", "code", "address", "contact_email", "contact_phone"]
    ordering_fields = ["name", "code", "is_active"]
