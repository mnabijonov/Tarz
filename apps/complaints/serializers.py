
from rest_framework import serializers
from .models import Complaint


class ComplaintSerializer(serializers.ModelSerializer):

    class Meta:
        model = Complaint
        fields = [
            "id",
            "order",
            "author",
            "reason",
            "status",
            "resolved_by",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "author",
            "status",
            "resolved_by",
            "created_at",
        ]

    def validate_reason(self, value):
        value = value.strip()

        if len(value) < 10:
            raise serializers.ValidationError(
                "Shikoyat matni kamida 10 ta belgidan iborat bo‘lishi kerak."
            )

        if len(value) > 5000:
            raise serializers.ValidationError(
                "Shikoyat matni 5000 ta belgidan oshmasligi kerak."
            )

        return value
