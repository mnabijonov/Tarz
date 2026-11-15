
from rest_framework import serializers
from .models import Category, District


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "name_ru",
            "icon",
            "parent",
            "position",
            "is_active",
            "created_at",
        ]
        read_only_fields = fields


class DistrictSerializer(serializers.ModelSerializer):

    class Meta:
        model = District
        fields = [
            "id",
            "name",
            "name_ru",
            "city",
        ]
        read_only_fields = fields
