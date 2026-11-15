from decimal import Decimal
from django.db import transaction
from django.db.models import Avg
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from apps.orders.models import Order
from apps.users.permissions import IsClient, NotBlocked
from .models import Review
from .serializers import ReviewSerializer



class ReviewCreateView(generics.CreateAPIView):
  
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated, NotBlocked, IsClient]

    def perform_create(self, serializer):
        user = self.request.user
        order = serializer.validated_data['order']
        if order.client_id != user.id:
            raise ValidationError("Bu buyurtma sizniki emas.")
        if order.status != Order.StatusChoice.COMPLETED or not order.selected_bid_id:
            raise ValidationError("Faqat yakunlangan buyurtmani baholash mumkin.")
        if Review.objects.filter(order=order, author=user).exists():
            raise ValidationError("Siz bu buyurtmani allaqachon baholagansiz.")

        master = order.selected_bid.master
        with transaction.atomic():
            serializer.save(author=user, target=master)
            avg = Review.objects.filter(target=master).aggregate(a=Avg('rating'))['a']
            master.rating_avg = Decimal(str(avg)).quantize(Decimal('0.1'))
            master.save(update_fields=['rating_avg'])



class MasterReviewsListView(generics.ListAPIView):
   
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated, NotBlocked]

    def get_queryset(self):
        return Review.objects.filter(target_id=self.kwargs['pk']).select_related('author').order_by('-created_at')