"""Governance APIs: policies, acknowledgements, audits, compliance issues."""
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.v1.permissions import CanManage
from apps.environmental.v1.models import Department

from .models import Audit, ComplianceIssue, ESGPolicy, PolicyAcknowledgement

User = get_user_model()


class ESGPolicySerializer(serializers.ModelSerializer):
    pillar_label = serializers.CharField(source="get_pillar_display", read_only=True)

    class Meta:
        model = ESGPolicy
        fields = ("id", "public_id", "title", "pillar", "pillar_label",
                  "version", "effective_date", "is_active")


class PolicyAcknowledgementSerializer(serializers.ModelSerializer):
    policy_title = serializers.CharField(source="policy.title", read_only=True)
    employee_name = serializers.CharField(source="employee.get_full_name", read_only=True)

    class Meta:
        model = PolicyAcknowledgement
        fields = ("id", "public_id", "policy_title", "employee_name",
                  "acknowledged_at", "is_acknowledged")


class AuditSerializer(serializers.ModelSerializer):
    department = serializers.PrimaryKeyRelatedField(queryset=Department.objects.all())
    department_name = serializers.CharField(source="department.name", read_only=True)
    audit_type_label = serializers.CharField(source="get_audit_type_display", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Audit
        fields = ("id", "public_id", "title", "department", "department_name", "audit_type",
                  "audit_type_label", "scheduled_date", "status", "status_label")


class ComplianceIssueSerializer(serializers.ModelSerializer):
    audit = serializers.PrimaryKeyRelatedField(queryset=Audit.objects.all())
    audit_title = serializers.CharField(source="audit.title", read_only=True)
    owner = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    owner_name = serializers.CharField(source="owner.get_full_name", read_only=True)
    severity_label = serializers.CharField(source="get_severity_display", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = ComplianceIssue
        fields = ("id", "public_id", "title", "description", "audit", "audit_title",
                  "owner", "owner_name", "severity", "severity_label", "due_date",
                  "status", "status_label", "is_overdue")


class ESGPolicyViewSet(viewsets.ModelViewSet):
    queryset = ESGPolicy.objects.all()
    serializer_class = ESGPolicySerializer
    permission_classes = [CanManage]
    http_method_names = ["get", "post"]


class PolicyAcknowledgementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PolicyAcknowledgement.objects.select_related("policy", "employee").all()
    serializer_class = PolicyAcknowledgementSerializer

    @action(detail=True, methods=["post"])
    def acknowledge(self, request, pk=None):
        ack = self.get_object()
        if not ack.acknowledged_at:
            ack.acknowledged_at = timezone.now()
            ack.save(update_fields=["acknowledged_at", "updated_at"])
        return Response(self.get_serializer(ack).data)


class AuditViewSet(viewsets.ModelViewSet):
    queryset = Audit.objects.select_related("department").all()
    serializer_class = AuditSerializer
    permission_classes = [CanManage]
    http_method_names = ["get", "post"]

    def perform_create(self, serializer):
        serializer.save(auditor=self.request.user)


class ComplianceIssueViewSet(viewsets.ModelViewSet):
    queryset = ComplianceIssue.objects.select_related("audit", "owner").all()
    serializer_class = ComplianceIssueSerializer
    permission_classes = [CanManage]
    http_method_names = ["get", "post"]
