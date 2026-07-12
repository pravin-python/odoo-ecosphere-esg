"""Environmental read APIs (RLS-scoped list endpoints for the module tables)."""
from rest_framework import serializers, viewsets

from .models import CarbonTransaction, Department, EmissionFactor, SustainabilityGoal


class EmissionFactorSerializer(serializers.ModelSerializer):
    source_type_label = serializers.CharField(source="get_source_type_display", read_only=True)
    unit_label = serializers.CharField(source="get_unit_display", read_only=True)

    class Meta:
        model = EmissionFactor
        fields = ("id", "public_id", "name", "source_type", "source_type_label",
                  "unit", "unit_label", "factor_value", "effective_from", "is_active")


class CarbonTransactionSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True)
    source_type_label = serializers.CharField(source="get_source_type_display", read_only=True)

    class Meta:
        model = CarbonTransaction
        fields = ("id", "public_id", "department_name", "source_type", "source_type_label",
                  "quantity", "co2e_kg", "occurred_on", "created_at")


class SustainabilityGoalSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True, default="—")
    metric_label = serializers.CharField(source="get_metric_display", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = SustainabilityGoal
        fields = ("id", "public_id", "title", "department_name", "metric", "metric_label",
                  "baseline_value", "target_value", "target_date", "status", "status_label")


class DepartmentSerializer(serializers.ModelSerializer):
    manager_name = serializers.CharField(source="manager.get_full_name", read_only=True, default="—")

    class Meta:
        model = Department
        fields = ("id", "public_id", "name", "code", "manager_name",
                  "total_co2e_kg", "esg_score", "is_active")


class EmissionFactorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EmissionFactor.objects.all()
    serializer_class = EmissionFactorSerializer


class CarbonTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CarbonTransaction.objects.select_related("department").all()
    serializer_class = CarbonTransactionSerializer


class SustainabilityGoalViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SustainabilityGoal.objects.select_related("department").all()
    serializer_class = SustainabilityGoalSerializer


class DepartmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Department.objects.select_related("manager").all()
    serializer_class = DepartmentSerializer
