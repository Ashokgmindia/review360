from rest_framework import serializers
from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("email", "password", "first_name", "last_name")

    def create(self, validated_data):
        password = validated_data.pop("password")
        email = validated_data.get("email")
        username = email
        user = User.objects.create_user(username=username, **validated_data)
        user.set_password(password)
        user.save()
        return user


class EmailTokenObtainSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


