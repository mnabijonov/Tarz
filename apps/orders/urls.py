
from django.urls import path

from .views import (
    MasterFeedView,
    MasterJobsView,
    OrderCancelView,
    OrderDetailView,
    OrderFinishView,
    OrderListCreateView,
    OrderPhotoCreateView,
    OrderStartView,
)

urlpatterns = [
    path("orders/", OrderListCreateView.as_view(), name="order-list"),
    path("orders/feed/", MasterFeedView.as_view(), name="order-feed"),
    path("orders/my-jobs/", MasterJobsView.as_view(), name="order-my-jobs"),
    path("orders/photos/", OrderPhotoCreateView.as_view(), name="order-photo-create"),
    path("orders/<int:pk>/", OrderDetailView.as_view(), name="order-detail"),
    path("orders/<int:pk>/cancel/", OrderCancelView.as_view(), name="order-cancel"),
    path("orders/<int:pk>/start/", OrderStartView.as_view(), name="order-start"),
    path("orders/<int:pk>/finish/", OrderFinishView.as_view(), name="order-finish"),
]
