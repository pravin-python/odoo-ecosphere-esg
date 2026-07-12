"""Social APIs: CSR activity catalog + employee participation with evidence upload."""
from collections import Counter

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.v1.enums import ApprovalStatus

from .models import CSRActivity, EmployeeParticipation


class DiversityView(APIView):
    """Workforce diversity summary (Social → Diversity Dashboard).

    Scoped to the caller's department unless they hold a privileged role.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        User = get_user_model()
        user = request.user
        privileged = user.is_superuser or getattr(user, "role", None) in ("ADMIN", "GOVERNANCE_OFFICER")

        users = User.objects.filter(is_active=True)
        if not privileged and user.department_id:
            users = users.filter(department_id=user.department_id)

        role_labels = dict(User._meta.get_field("role").choices)
        by_role = [
            {"label": role_labels.get(r, r or "—"), "count": n}
            for r, n in Counter(users.values_list("role", flat=True)).items()
        ]
        by_department = [
            {"label": name or "Unassigned", "count": n}
            for name, n in Counter(users.values_list("department__name", flat=True)).items()
        ]
        headcount = users.count()
        participants = (
            EmployeeParticipation.objects.filter(status=ApprovalStatus.APPROVED)
            .values("employee").distinct().count()
        )
        rate = round(participants / headcount * 100, 1) if headcount else 0.0

        return Response({
            "headcount": headcount,
            "csr_participation_rate": rate,
            "by_role": sorted(by_role, key=lambda x: -x["count"]),
            "by_department": sorted(by_department, key=lambda x: -x["count"]),
        })


class CSRActivitySerializer(serializers.ModelSerializer):
    category_label = serializers.CharField(source="get_category_display", read_only=True)
    participant_count = serializers.IntegerField(source="participations.count", read_only=True)

    class Meta:
        model = CSRActivity
        fields = ("id", "public_id", "title", "description", "category", "category_label",
                  "xp_reward", "start_date", "end_date", "is_active", "participant_count")


class EmployeeParticipationSerializer(serializers.ModelSerializer):
    activity = serializers.PrimaryKeyRelatedField(queryset=CSRActivity.objects.all())
    activity_title = serializers.CharField(source="activity.title", read_only=True)
    employee_name = serializers.CharField(source="employee.get_full_name", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    proof_url = serializers.FileField(source="proof_file", read_only=True)

    class Meta:
        model = EmployeeParticipation
        fields = ("id", "public_id", "activity", "activity_title", "employee_name",
                  "proof_file", "proof_url", "status", "status_label",
                  "review_notes", "created_at")
        extra_kwargs = {"proof_file": {"write_only": True, "required": False}}

    def validate(self, attrs):
        from apps.system_core.v1.models import GlobalConfiguration

        if GlobalConfiguration.load().strict_evidence_required and not attrs.get("proof_file"):
            raise serializers.ValidationError(
                {"proof_file": "Evidence upload (image/PDF) is required to participate."}
            )
        return attrs


class CSRActivityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CSRActivity.objects.all()
    serializer_class = CSRActivitySerializer


class EmployeeParticipationViewSet(viewsets.ModelViewSet):
    """List the approval queue and let employees submit participation.

    RLS restricts rows to the owner (employee) or their department manager, so
    the same endpoint safely serves both the employee's history and a manager's
    review queue.
    """

    queryset = EmployeeParticipation.objects.select_related("activity", "employee").all()
    serializer_class = EmployeeParticipationSerializer
    parser_classes = [MultiPartParser, FormParser]
    http_method_names = ["get", "post"]

    def perform_create(self, serializer):
        # The owner is always the caller — never trust a client-supplied employee id.
        serializer.save(employee=self.request.user, status=ApprovalStatus.PENDING)

    def _review(self, request, new_status):
        participation = self.get_object()
        if participation.status == ApprovalStatus.APPROVED:
            return Response({"detail": "Already approved."}, status=status.HTTP_400_BAD_REQUEST)
        participation.status = new_status
        participation.reviewed_by = request.user
        participation.reviewed_at = timezone.now()
        participation.review_notes = request.data.get("notes", "")
        participation.save()  # APPROVED fires the XP-award signal
        return Response(self.get_serializer(participation).data)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        return self._review(request, ApprovalStatus.APPROVED)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        return self._review(request, ApprovalStatus.REJECTED)
