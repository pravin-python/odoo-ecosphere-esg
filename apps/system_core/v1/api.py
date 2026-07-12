"""Master-data APIs: products, categories, global config, user choices."""
from django.contrib.auth import get_user_model
from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.v1.permissions import CanManage

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


class UserChoicesView(APIView):
    """Lightweight user list for owner/assignee dropdowns (id + display name).

    Scoped to the caller's department unless they hold a privileged role.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        User = get_user_model()
        user = request.user
        privileged = user.is_superuser or getattr(user, "role", None) in ("ADMIN", "GOVERNANCE_OFFICER")
        qs = User.objects.filter(is_active=True)
        if not privileged and user.department_id:
            qs = qs.filter(department_id=user.department_id)
        return Response([
            {"id": u.id, "name": u.get_full_name() or u.username}
            for u in qs.order_by("username")
        ])


class ProductESGProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductESGProfile
        fields = ("id", "public_id", "name", "sku", "carbon_footprint_kg",
                  "recyclable", "ethical_sourcing_score", "is_active")

    def validate_ethical_sourcing_score(self, value):
        if not 0 <= value <= 100:
            raise serializers.ValidationError("Score must be between 0 and 100.")
        return value


class CategorySerializer(serializers.ModelSerializer):
    type_label = serializers.CharField(source="get_type_display", read_only=True)

    class Meta:
        model = Category
        fields = ("id", "public_id", "name", "type", "type_label", "description", "is_active")


class ProductESGProfileViewSet(viewsets.ModelViewSet):
    queryset = ProductESGProfile.objects.all()
    serializer_class = ProductESGProfileSerializer
    permission_classes = [CanManage]
    http_method_names = ["get", "post"]


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [CanManage]
    http_method_names = ["get", "post"]
