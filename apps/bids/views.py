from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.masters.models import MasterProfile
from apps.orders.models import Order
from apps.orders.serializers import OrderSerializers
from apps.orders.services import select_bid
from apps.users.services import contact_info
from apps.users.permissions import IsApprovedMaster, IsClient, NotBlocked
from .models import Bid
from .serializers import BidSerializer, BidUpdateSerializer, BidWithMasterSerializer

from drf_spectacular.utils import extend_schema

MAX_BIDS_PER_ORDER = 7


class BidCreateView(generics.CreateAPIView):
    
    serializer_class = BidSerializer
    permission_classes = [IsAuthenticated, NotBlocked, IsApprovedMaster]

    def perform_create(self, serializer):
        master = MasterProfile.objects.get(user=self.request.user)
        with transaction.atomic():
            order = Order.objects.select_for_update().get(pk=serializer.validated_data['order'].pk)
            if order.status != Order.StatusChoice.NEW:
                raise ValidationError("Bu buyurtma taklif qabul qilmaydi.")
            if order.client_id == self.request.user.pk:
                raise ValidationError("O'z buyurtmangizga taklif yubora olmaysiz.")
            if order.bids.count() >= MAX_BIDS_PER_ORDER:
                raise ValidationError(f"Bu buyurtma uchun {MAX_BIDS_PER_ORDER} ta taklif to'lgan.")
            if order.bids.filter(master=master).exists():
                raise ValidationError("Siz bu buyurtmaga allaqachon taklif yuborgansiz.")
            category_ids = [order.category_id, order.category.parent_id if order.category else None]
            if not master.categories.filter(pk__in=[c for c in category_ids if c]).exists() or \
               not master.districts.filter(pk=order.district_id).exists():
                raise ValidationError("Bu buyurtma sizning kategoriya yoki hududingizga mos emas.")
            serializer.save(master=master, order=order)



class MyBidsListView(generics.ListAPIView):
    
    serializer_class = BidSerializer
    permission_classes = [IsAuthenticated, NotBlocked, IsApprovedMaster]

    def get_queryset(self):
        return Bid.objects.filter(master__user=self.request.user).order_by('-created_at')



class BidUpdateView(generics.UpdateAPIView):
    
    serializer_class = BidUpdateSerializer
    permission_classes = [IsAuthenticated, NotBlocked, IsApprovedMaster]
    http_method_names = ['patch', 'options']

    def get_queryset(self):
        return Bid.objects.filter(master__user=self.request.user)

    def perform_update(self, serializer):
        bid = serializer.instance
        if bid.status != Bid.StatusChoice.PENDING or bid.order.status != Order.StatusChoice.NEW:
            raise ValidationError("Taklifni endi tahrirlab bo'lmaydi.")
        serializer.save()



class OrderBidsListView(generics.ListAPIView):
   
    serializer_class = BidWithMasterSerializer
    permission_classes = [IsAuthenticated, NotBlocked, IsClient]
    pagination_class = None

    def get_queryset(self):
        order = get_object_or_404(Order, pk=self.kwargs['order_pk'], client=self.request.user)
        return order.bids.select_related('master__user').order_by('price')



class BidSelectView(APIView):
    
    permission_classes = [IsAuthenticated, NotBlocked, IsClient]

    def post(self, request, pk):
        with transaction.atomic():
            bid = get_object_or_404(
                Bid.objects.select_related('master__user'),
                pk=pk, order__client=request.user,
            )
            order = Order.objects.select_for_update().get(pk=bid.order_id)
            if order.status != Order.StatusChoice.NEW:
                raise ValidationError("Bu buyurtma uchun usta allaqachon tanlangan yoki u yopilgan.")
            if bid.status != Bid.StatusChoice.PENDING:
                raise ValidationError("Bu taklif amal qilmaydi.")

            # M6: ustalarga bildirishnoma ham shu yerda (on_commit) rejalashtiriladi
            select_bid(order, bid)

        master_user = bid.master.user
        master_contact = contact_info(master_user)
        master_contact['master_id'] = bid.master.pk
        return Response({
            'order': OrderSerializers(order, context={'request': request}).data,
            'master': master_contact,
        })