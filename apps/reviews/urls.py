from django.urls import path
from .views import MasterReviewsListView, ReviewCreateView

urlpatterns = [
    path('reviews/', ReviewCreateView.as_view(), name='review-create'),
    path('masters/<int:pk>/reviews/', MasterReviewsListView.as_view(), name='master-reviews'),
]