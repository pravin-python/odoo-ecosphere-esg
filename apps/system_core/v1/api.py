"""Master-data read APIs: products and categories (Settings + Environmental)."""
from rest_framework import serializers, viewsets

from .models import Category, ProductESGProfile


class ProductESGProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductESGProfile
        fields = ("id", "public_id", "name", "sku", "carbon_footprint_kg",
                  "recyclable", "ethical_sourcing_score", "is_active")


class CategorySerializer(serializers.ModelSerializer):
    type_label = serializers.CharField(source="get_type_display", read_only=True)

    class Meta:
        model = Category
        fields = ("id", "public_id", "name", "type", "type_label", "description", "is_active")


class ProductESGProfileViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ProductESGProfile.objects.all()
    serializer_class = ProductESGProfileSerializer


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
