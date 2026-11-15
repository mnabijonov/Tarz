from django.urls import path

from .views import (
    BidCreateView,
    BidSelectView,
    BidUpdateView,
    MyBidsListView,
    OrderBidsListView,
)

urlpatterns = [
    path('bids/', BidCreateView.as_view(), name='bid-create'),
    path('bids/my/', MyBidsListView.as_view(), name='bid-my'),
    path('bids/<int:pk>/', BidUpdateView.as_view(), name='bid-update'),
    path('bids/<int:pk>/select/', BidSelectView.as_view(), name='bid-select'),
    path('bids/<int:order_pk>/bids/', OrderBidsListView.as_view(), name='order-bids'),
]