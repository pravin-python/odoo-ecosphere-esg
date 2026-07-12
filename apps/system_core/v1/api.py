"""Master-data read APIs: products, categories, and global config (Settings)."""
from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Category, GlobalConfiguration, ProductESGProfile


class GlobalConfigView(APIView):
    """Read the platform configuration singleton (Settings → ESG Configuration)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        c = GlobalConfiguration.load()
        return Response({
            "current_reporting_year": c.current_reporting_year,
            "auto_emission_enabled": c.auto_emission_enabled,
            "strict_evidence_required": c.strict_evidence_required,
            "badge_auto_award_enabled": getattr(c, "badge_auto_award_enabled", True),
            "default_carbon_reduction_target": float(c.default_carbon_reduction_target),
            "weight_environmental": getattr(c, "weight_environmental", 40),
            "weight_social": getattr(c, "weight_social", 30),
            "weight_governance": getattr(c, "weight_governance", 30),
        })


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
