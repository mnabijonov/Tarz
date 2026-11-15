
from rest_framework import serializers

from apps.users.services import validate_image_file

from .models import MasterProfile, PortfolioPhoto
from .services import approval_problems


class MasterProfileSerializer(serializers.ModelSerializer):

    # U1: frontend shu ro'yxat bo'yicha "profilni to'ldiring" deb ko'rsatadi
    missing_requirements = serializers.SerializerMethodField()

    class Meta:
        model = MasterProfile

        fields = [
            "id",
            "user",
            "categories",
            "districts",
            "experience_years",
            "bio",
            "document_photo",
            "status",
            "rejection_reason",
            "rating_avg",
            "jobs_done",
            "is_busy",
            "missing_requirements",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "user",
            "status",
            "rejection_reason",
            "rating_avg",
            "jobs_done",
            "created_at",
            "updated_at",
        ]

    def get_missing_requirements(self, obj):
        request = self.context.get("request")
        language = getattr(getattr(request, "user", None), "language", "uz")
        return approval_problems(obj, language)

    def validate_document_photo(self, value):
        return validate_image_file(value)

    def validate_experience_years(self, value):
        if value < 0 or value > 70:
            raise serializers.ValidationError(
                "Tajriba 0 dan 70 yilgacha bo'lishi kerak."
            )

        return value

    def validate_bio(self, value):
        value = value.strip()

        if len(value) > 3000:
            raise serializers.ValidationError(
                "Usta haqida ma'lumot 3000 belgidan oshmasligi kerak."
            )

        return value

    def update(self, instance, validated_data):

        categories_changed = (
            "categories" in validated_data
            and set(
                validated_data["categories"]
            ) != set(instance.categories.all())
        )

        districts_changed = (
            "districts" in validated_data
            and set(
                validated_data["districts"]
            ) != set(instance.districts.all())
        )

        document_changed = (
            "document_photo" in validated_data
        )

        needs_review = (
            categories_changed
            or districts_changed
            or document_changed
        )

        if needs_review:
            validated_data["status"] = (
                MasterProfile.StatusChoice.PENDING
            )
            validated_data["rejection_reason"] = ""

        return super().update(instance, validated_data)


class PortfolioPhotoSerializer(serializers.ModelSerializer):

    class Meta:
        model = PortfolioPhoto

        fields = [
            "id",
            "master",
            "image",
            "caption",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "master",
            "created_at",
        ]

    def validate_image(self, value):
        return validate_image_file(value)

    def validate_caption(self, value):
        return value.strip()


class MasterPublicSerializer(serializers.ModelSerializer):

    full_name = serializers.SerializerMethodField()

    portfolio_photos = PortfolioPhotoSerializer(
        many=True,
        read_only=True,
    )

    is_verified = serializers.SerializerMethodField()

    class Meta:
        model = MasterProfile

        fields = [
            "id",
            "full_name",
            "categories",
            "districts",
            "experience_years",
            "bio",
            "rating_avg",
            "jobs_done",
            "is_busy",
            "is_verified",
            "portfolio_photos",
        ]

        read_only_fields = fields

    def get_full_name(self, obj):
        return (
            obj.user.get_full_name()
            or obj.user.username
        )

    def get_is_verified(self, obj):
        return (
            obj.status == MasterProfile.StatusChoice.ACCEPTED
        )
