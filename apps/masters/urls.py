
from django.urls import path

from .views import (
    MasterPublicDetailView,
    MyMasterProfileView,
    MyPortfolioDetailView,
    MyPortfolioListCreateView,
)


urlpatterns = [
    path("masters/me/", MyMasterProfileView.as_view(), name="master-me"),
    path("masters/me/portfolio/", MyPortfolioListCreateView.as_view(), name="master-portfolio"),
    path("masters/me/portfolio/<int:pk>/", MyPortfolioDetailView.as_view(), name="master-portfolio-detail"),
    path("masters/<int:pk>/", MasterPublicDetailView.as_view(), name="master-detail"),
]
