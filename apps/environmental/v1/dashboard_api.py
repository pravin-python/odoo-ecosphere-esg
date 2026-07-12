"""Executive dashboard summary API.

Returns everything the Dashboard screen needs in one round-trip. All queries are
RLS-scoped automatically, so a manager sees only their department's figures.
"""
from datetime import timedelta
from decimal import Decimal

from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _avg(values):
    values = [Decimal(str(v)) for v in values if v is not None]
    if not values:
        return Decimal("50")
    return sum(values) / len(values)


class DashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.compliance.v1.models import ComplianceIssue
        from apps.core.v1.enums import ApprovalStatus
        from apps.engagement.v1.models import EmployeeProfile
        from apps.notifications.v1.models import Notification
        from apps.social_impact.v1.models import EmployeeParticipation

        from . import scoring
        from .models import CarbonTransaction, Department

        today = timezone.now().date()
        depts = list(Department.objects.all())  # RLS-scoped to the viewer

        # ── Pillar scores (org-wide within the viewer's scope) ──
        if depts:
            max_co2e = max((d.total_co2e_kg or 0) for d in depts)
            env = _avg([scoring.environmental_score(d, max_department_co2e=max_co2e) for d in depts])
            soc = _avg([scoring.social_score(d) for d in depts])
            gov = _avg([scoring.governance_score(d) for d in depts])
        else:
            env = soc = gov = Decimal("50")
        we, ws, wg = _weights()
        overall = (env * we + soc * ws + gov * wg) / (we + ws + wg)

        # ── Emissions trend: last 12 months of CO2e ──
        start = today.replace(day=1) - timedelta(days=365)
        buckets = (
            CarbonTransaction.objects.filter(occurred_on__gte=start)
            .annotate(m=TruncMonth("occurred_on"))
            .values("m")
            .annotate(total=Sum("co2e_kg"))
            .order_by("m")
        )
        by_month = {b["m"].strftime("%Y-%m"): float(b["total"] or 0) for b in buckets}
        trend = []
        cursor = start
        for _ in range(13):
            key = cursor.strftime("%Y-%m")
            trend.append({"label": _MONTHS[cursor.month - 1], "value": by_month.get(key, 0.0)})
            cursor = (cursor.replace(day=1) + timedelta(days=32)).replace(day=1)

        # ── Department ranking (greenest / lowest emissions first is subjective;
        #    show absolute footprint so the biggest emitters stand out) ──
        ranking = [
            {"name": d.name, "co2e": float(d.total_co2e_kg or 0)}
            for d in sorted(depts, key=lambda x: x.total_co2e_kg or 0, reverse=True)[:6]
        ]

        # ── Headline counts ──
        profile = EmployeeProfile.objects.filter(user=request.user).first()
        carbon_30d = (
            CarbonTransaction.objects.filter(occurred_on__gte=today - timedelta(days=30))
            .aggregate(s=Sum("co2e_kg"))["s"]
            or 0
        )

        recent = [
            {"title": n.title, "category": n.category, "when": n.created_at.isoformat()}
            for n in Notification.objects.filter(recipient=request.user)[:6]
        ]

        return Response({
            "scores": {
                "environmental": float(env), "social": float(soc),
                "governance": float(gov), "overall": float(overall),
            },
            "emissions_trend": trend,
            "department_ranking": ranking,
            "counts": {
                "carbon_30d_kg": float(carbon_30d),
                "open_compliance": ComplianceIssue.objects.exclude(
                    status=ComplianceIssue.Status.RESOLVED).count(),
                "overdue_compliance": ComplianceIssue.objects.overdue().count(),
                "csr_pending": EmployeeParticipation.objects.filter(
                    status=ApprovalStatus.PENDING).count(),
                "my_xp": profile.xp_balance if profile else 0,
            },
            "recent_activity": recent,
        })


def _weights():
    try:
        from apps.system_core.v1.models import GlobalConfiguration

        cfg = GlobalConfiguration.load()
        return (Decimal(cfg.weight_environmental), Decimal(cfg.weight_social),
                Decimal(cfg.weight_governance))
    except Exception:
        return (Decimal("40"), Decimal("30"), Decimal("30"))
