
from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from apps.users.permissions import IsMaster, NotBlocked

from .models import MasterProfile, PortfolioPhoto
from .serializers import (
    MasterProfileSerializer,
    MasterPublicSerializer,
    PortfolioPhotoSerializer,
)
from .services import MAX_PORTFOLIO_PHOTOS, MIN_PORTFOLIO_PHOTOS


class MyMasterProfileView(generics.RetrieveUpdateAPIView):

    serializer_class = MasterProfileSerializer

    permission_classes = [
        IsAuthenticated,
        NotBlocked,
        IsMaster,
    ]

    def get_object(self):
        profile, created = MasterProfile.objects.get_or_create(
            user=self.request.user,
        )

        return profile


class MasterPublicDetailView(generics.RetrieveAPIView):

    serializer_class = MasterPublicSerializer

    permission_classes = [
        IsAuthenticated,
        NotBlocked,
    ]

    queryset = (
        MasterProfile.objects
        .filter(
            status=MasterProfile.StatusChoice.ACCEPTED,
        )
        .select_related("user")
        .prefetch_related(
            "portfolio_photos",
            "categories",
            "districts",
        )
    )


class MyPortfolioListCreateView(generics.ListCreateAPIView):

    serializer_class = PortfolioPhotoSerializer

    permission_classes = [
        IsAuthenticated,
        NotBlocked,
        IsMaster,
    ]

    pagination_class = None

    def get_queryset(self):
        return (
            PortfolioPhoto.objects
            .filter(master__user=self.request.user)
            .select_related("master")
        )

    def perform_create(self, serializer):

        with transaction.atomic():

            profile = get_object_or_404(
                MasterProfile.objects.select_for_update(),
                user=self.request.user,
            )

            photo_count = profile.portfolio_photos.count()

            if photo_count >= MAX_PORTFOLIO_PHOTOS:
                raise ValidationError(
                    {
                        "image": (
                            f"Portfolioda ko'pi bilan "
                            f"{MAX_PORTFOLIO_PHOTOS} ta rasm "
                            "bo'lishi mumkin."
                        )
                    }
                )

            serializer.save(master=profile)


class MyPortfolioDetailView(generics.DestroyAPIView):

    permission_classes = [
        IsAuthenticated,
        NotBlocked,
        IsMaster,
    ]

    def get_queryset(self):
        return PortfolioPhoto.objects.filter(
            master__user=self.request.user,
        )

    def perform_destroy(self, instance):
        with transaction.atomic():
            profile = MasterProfile.objects.select_for_update().get(pk=instance.master_id)

            # U1: tasdiqlangan usta portfoliosi 3 tadan kamayib qolmasin
            if (
                profile.status == MasterProfile.StatusChoice.ACCEPTED
                and profile.portfolio_photos.count() <= MIN_PORTFOLIO_PHOTOS
            ):
                raise ValidationError(
                    f"Portfolioda kamida {MIN_PORTFOLIO_PHOTOS} ta rasm qolishi kerak. "
                    "Avval yangi rasm yuklang."
                )

            instance.delete()
