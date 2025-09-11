from django.contrib.auth import authenticate, get_user_model
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import RegisterSerializer, EmailTokenObtainSerializer


class RegisterView(generics.CreateAPIView):
    permission_classes = (IsAdminUser,)
    serializer_class = RegisterSerializer


class EmailTokenObtainPairView(generics.GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = EmailTokenObtainSerializer

    def post(self, request, *args, **kwargs):
        email = request.data.get("email")
        password = request.data.get("password")
        # Allow login by email (map to username internally)
        User = get_user_model()
        try:
            user_obj = User.objects.get(email=email)
            username = user_obj.username
        except User.DoesNotExist:
            username = email
        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        refresh = RefreshToken.for_user(user)
        return Response({"refresh": str(refresh), "access": str(refresh.access_token)})


