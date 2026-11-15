
from django.db.models import Q

from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from .models import Complaint
from .serializers import ComplaintSerializer


class ComplaintListCreateView(generics.ListCreateAPIView):

    serializer_class = ComplaintSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Complaint.objects
            .filter(author=self.request.user)
            .select_related(
                "order",
                "author",
                "resolved_by",
            )
            .order_by("-created_at")
        )

    def perform_create(self, serializer):
        user = self.request.user
        order = serializer.validated_data.get("order")

        if order is not None:
            is_client = order.client_id == user.id

            is_selected_master = (
                order.selected_bid is not None
                and order.selected_bid.master.user_id == user.id
            )

            if not (is_client or is_selected_master):
                raise ValidationError(
                    "Bu buyurtma bo‘yicha shikoyat yuborish huquqingiz yo‘q."
                )

        serializer.save(author=user)
