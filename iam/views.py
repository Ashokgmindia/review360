from django.contrib.auth import authenticate
from rest_framework import generics, status, viewsets, permissions, filters
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema_view, extend_schema

from .serializers import RegisterSerializer, EmailTokenObtainSerializer, CollegeSerializer
from .models import College, User
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


@extend_schema(tags=["IAM"])
class MeView(generics.RetrieveAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user = request.user
        college_ids = []
        try:
            college_ids = list(getattr(user, "colleges").values_list("id", flat=True))
        except Exception:
            college_ids = []
        if user.college_id:
            college_ids.append(user.college_id)
        data = {
            "id": user.id,
            "email": user.email,
            "role": getattr(user, "role", None),
            "college": user.college_id,
            "colleges": list(sorted(set(college_ids))),
        }
        return Response(data)


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

    def perform_create(self, serializer):
        # Only superadmins can create colleges
        if getattr(self.request.user, "role", None) != User.Role.SUPERADMIN:
            raise serializers.ValidationError({"detail": "Only Super Admin can create colleges."})
        college = serializer.save()

    def perform_update(self, serializer):
        college = serializer.save()
        admin = college.admin
        if admin is not None:
            admin.role = User.Role.COLLEGE_ADMIN
            admin.college = college
            admin.save()
            try:
                # Ensure M2M membership is in sync
                admin.colleges.add(college)
            except Exception:
                pass

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if getattr(user, "role", None) == User.Role.SUPERADMIN:
            return qs
        if getattr(user, "role", None) == User.Role.COLLEGE_ADMIN:
            user_college_ids = []
            try:
                user_college_ids = list(getattr(user, "colleges").values_list("id", flat=True))
            except Exception:
                user_college_ids = []
            if user.college_id:
                user_college_ids.append(user.college_id)
            user_college_ids = list({cid for cid in user_college_ids if cid})
            if user_college_ids:
                return qs.filter(id__in=user_college_ids)
            return qs.none()
        # Other roles cannot view colleges list by default
        return qs.none()


@extend_schema(tags=["IAM"])
class IamTokenObtainPairView(TokenObtainPairView):
    pass


@extend_schema(tags=["IAM"])
class IamTokenRefreshView(TokenRefreshView):
    pass


