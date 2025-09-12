from django.contrib.auth import authenticate
from rest_framework import generics, status, viewsets, permissions, filters
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema_view, extend_schema

from .serializers import RegisterSerializer, EmailTokenObtainSerializer
from .models import College
from .serializers import RegisterSerializer
from rest_framework import serializers


class EmailTokenObtainPairView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = EmailTokenObtainSerializer

    @extend_schema(tags=["IAM"])
    def post(self, request, *args, **kwargs):
        email = request.data.get("email")
        password = request.data.get("password")
        try:
            from .models import User
            user_obj = User.objects.get(email=email)
            username = user_obj.username
        except User.DoesNotExist:
            username = email
        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        refresh = RefreshToken.for_user(user)
        return Response({"refresh": str(refresh), "access": str(refresh.access_token)})


class RegisterView(generics.CreateAPIView):
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = RegisterSerializer

    @extend_schema(tags=["IAM"])
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class CollegeSerializer(serializers.ModelSerializer):
    class Meta:
        model = College
        fields = [
            "id",
            "name",
            "code",
            "address",
            "contact_email",
            "contact_phone",
            "is_active",
        ]
        read_only_fields = ["id"]


@extend_schema_view(
    list=extend_schema(tags=["IAM"]),
    retrieve=extend_schema(tags=["IAM"]),
    create=extend_schema(tags=["IAM"]),
    update=extend_schema(tags=["IAM"]),
    partial_update=extend_schema(tags=["IAM"]),
    destroy=extend_schema(tags=["IAM"]),
)
class CollegeViewSet(viewsets.ModelViewSet):
    queryset = College.objects.all().order_by("name")
    serializer_class = CollegeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["is_active", "code"]
    search_fields = ["name", "code", "address", "contact_email", "contact_phone"]
    ordering_fields = ["name", "code", "is_active"]


@extend_schema(tags=["IAM"])
class IamTokenObtainPairView(TokenObtainPairView):
    pass


@extend_schema(tags=["IAM"])
class IamTokenRefreshView(TokenRefreshView):
    pass


