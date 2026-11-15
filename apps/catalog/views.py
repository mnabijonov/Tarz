
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import Category, District
from .serializers import CategorySerializer, DistrictSerializer


class CategoryListView(generics.ListAPIView):

    queryset = (
        Category.objects
        .filter(is_active=True)
        .select_related("parent")
        .order_by("position", "name")
    )

    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None


class DistrictListView(generics.ListAPIView):

    queryset = District.objects.all().order_by("city", "name")

    serializer_class = DistrictSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
