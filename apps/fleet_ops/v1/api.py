"""Fleet ERP APIs. Creating a FleetLog auto-generates a CarbonTransaction
via the post_save signal — this is the demo's "ERP integration" hook."""
from rest_framework import serializers, viewsets

from apps.core.v1.permissions import CanManage
from apps.environmental.v1.models import Department

from .models import FleetLog, Vehicle


class VehicleSerializer(serializers.ModelSerializer):
    department = serializers.PrimaryKeyRelatedField(queryset=Department.objects.all())
    department_name = serializers.CharField(source="department.name", read_only=True)
    fuel_type_label = serializers.CharField(source="get_fuel_type_display", read_only=True)

    class Meta:
        model = Vehicle
        fields = ("id", "public_id", "name", "registration_no", "vehicle_type",
                  "fuel_type", "fuel_type_label", "department", "department_name", "is_active")


class FleetLogSerializer(serializers.ModelSerializer):
    vehicle = serializers.PrimaryKeyRelatedField(queryset=Vehicle.objects.all())
    vehicle_name = serializers.CharField(source="vehicle.name", read_only=True)

    class Meta:
        model = FleetLog
        fields = ("id", "public_id", "vehicle", "vehicle_name", "log_date",
                  "fuel_quantity", "distance_km", "notes")

    def validate_fuel_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Fuel quantity must be greater than zero.")
        return value


class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.select_related("department").all()
    serializer_class = VehicleSerializer
    permission_classes = [CanManage]
    http_method_names = ["get", "post"]


class FleetLogViewSet(viewsets.ModelViewSet):
    queryset = FleetLog.objects.select_related("vehicle").all()
    serializer_class = FleetLogSerializer
    permission_classes = [CanManage]
    http_method_names = ["get", "post"]

    def perform_create(self, serializer):
        serializer.save(logged_by=self.request.user)
