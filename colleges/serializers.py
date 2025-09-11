from rest_framework import serializers
from .models import College


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


