
from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User

        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "telegram_id",
            "telegram_username",
            "phone",
            "role",
            "language",
            "is_blocked",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "username",
            "telegram_id",
            "telegram_username",
            "phone",
            "role",
            "is_blocked",
            "created_at",
        ]


class SelectRoleSerializer(serializers.Serializer):

    role = serializers.ChoiceField(
        choices=[
            User.RoleChoice.CLIENT,
            User.RoleChoice.MASTER,
        ]
    )
