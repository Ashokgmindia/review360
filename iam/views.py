from django.contrib.auth import authenticate
from django.utils import timezone
from datetime import timedelta
from rest_framework import generics, status, viewsets, permissions, filters
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema_view, extend_schema
from academics import serializers

from .models import College, User
from .serializers import (
    RegisterSerializer, EmailTokenObtainSerializer, CollegeSerializer, MeSerializer,
    OTPVerifySerializer, PasswordResetRequestSerializer, PasswordResetConfirmSerializer
)
from .utils import generate_otp, send_otp_email


@extend_schema(tags=["IAM"])
class LoginView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = EmailTokenObtainSerializer
    throttle_scope = "login"

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get("email")
        password = serializer.validated_data.get("password")
        
        try:
            user_obj = User.objects.get(email=email)
            username = user_obj.username
        except User.DoesNotExist:
            return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
            
        user = authenticate(request, username=username, password=password)

        if user is None:
            return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        # Generate and send OTP
        otp = generate_otp()
        user.otp = otp
        user.otp_created_at = timezone.now()
        user.save()

        subject = 'Your One-Time Password (OTP) for Login'
        message_template = 'Your OTP for authentication is: {otp}\n\nThis code is valid for 5 minutes.'
        send_otp_email(user.email, otp, subject, message_template)

        return Response({"detail": "OTP sent to your email. Please verify to login."}, status=status.HTTP_200_OK)


@extend_schema(tags=["IAM"])
class OTPVerifyView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = OTPVerifySerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get("email")
        otp = serializer.validated_data.get("otp")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        if user.otp != otp:
            return Response({"detail": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)

        if timezone.now() > user.otp_created_at + timedelta(minutes=5):
            return Response({"detail": "OTP has expired."}, status=status.HTTP_400_BAD_REQUEST)

        # Clear OTP
        user.otp = None
        user.otp_created_at = None
        user.save()

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
    serializer_class = MeSerializer

    def get(self, request, *args, **kwargs):
        user = request.user
        college_ids = list(user.colleges.values_list("id", flat=True))
        if user.college_id:
            college_ids.append(user.college_id)
        
        data = {
            "id": user.id,
            "email": user.email,
            "role": getattr(user, "role", None),
            "college": user.college_id,
            "colleges": list(sorted(set(college_ids))),
        }
        serializer = self.get_serializer(data)
        return Response(serializer.data)


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
        if getattr(self.request.user, "role", None) != User.Role.SUPERADMIN:
            raise serializers.ValidationError({"detail": "Only Super Admin can create colleges."})
        serializer.save()

    def perform_update(self, serializer):
        college = serializer.save()
        admin = college.admin
        if admin is not None:
            if admin.role != User.Role.SUPERADMIN:
                admin.role = User.Role.COLLEGE_ADMIN
            admin.college = college
            admin.save()
            admin.colleges.add(college)

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not user or not user.is_authenticated:
            return qs.none()
        if getattr(user, "role", None) == User.Role.SUPERADMIN:
            return qs
        if getattr(user, "role", None) == User.Role.COLLEGE_ADMIN:
            college_ids = list(user.colleges.values_list("id", flat=True))
            if user.college_id:
                college_ids.append(user.college_id)
            if college_ids:
                return qs.filter(id__in=list(set(college_ids)))
        return qs.none()


@extend_schema(tags=["IAM"])
class PasswordResetRequestView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = PasswordResetRequestSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get("email")
        
        try:
            user = User.objects.get(email=email)
            otp = generate_otp()
            user.otp = otp
            user.otp_created_at = timezone.now()
            user.save()

            subject = 'Your Password Reset OTP'
            message_template = 'Your OTP for password reset is: {otp}\n\nThis code is valid for 5 minutes.'
            send_otp_email(user.email, otp, subject, message_template)
            
            return Response({"detail": "Password reset OTP sent to your email."}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            # Do not reveal if the user exists or not
            return Response({"detail": "If an account with that email exists, an OTP has been sent."}, status=status.HTTP_200_OK)

@extend_schema(tags=["IAM"])
class PasswordResetConfirmView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get("email")
        otp = serializer.validated_data.get("otp")
        new_password = serializer.validated_data.get("new_password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": "Invalid request."}, status=status.HTTP_400_BAD_REQUEST)

        if user.otp != otp:
            return Response({"detail": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)
        
        if timezone.now() > user.otp_created_at + timedelta(minutes=5):
            return Response({"detail": "OTP has expired."}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.otp = None
        user.otp_created_at = None
        user.save()

        return Response({"detail": "Password has been reset successfully."}, status=status.HTTP_200_OK)


@extend_schema(tags=["IAM"])
class IamTokenObtainPairView(TokenObtainPairView):
    pass


@extend_schema(tags=["IAM"])
class IamTokenRefreshView(TokenRefreshView):
    pass
