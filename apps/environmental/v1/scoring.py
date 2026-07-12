"""ESG Scoring Engine.

Turns raw operational data into comparable 0-100 scores per department, then
into a single Overall ESG Score for the organization.

Methodology (transparent and configurable):

  Environmental = 50% goal achievement + 50% relative emission performance
  Social        = CSR + Challenge participation rate of department members
  Governance    = 50% policy acknowledgement rate + 50% compliance health

  Department Total = weighted average of the three pillars, using the weights on
                     GlobalConfiguration (default E 40 / S 30 / G 30).
  Overall ESG      = mean of active departments' Total scores.

All pillar helpers return a Decimal in the range 0-100 and degrade gracefully to
a neutral 50 when there is no data to score against, so a brand-new org doesn't
show as failing.
"""
from decimal import Decimal, ROUND_HALF_UP

from django.utils import timezone

NEUTRAL = Decimal("50")
ZERO = Decimal("0")
HUNDRED = Decimal("100")


def _q(value) -> Decimal:
    """Clamp to 0-100 and round to 2 dp."""
    value = Decimal(str(value))
    value = max(ZERO, min(HUNDRED, value))
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# --------------------------------------------------------------------------- #
# Pillar calculations
# --------------------------------------------------------------------------- #
def environmental_score(department, *, max_department_co2e=None) -> Decimal:
    from .models import CarbonTransaction, Department, SustainabilityGoal

    goals = SustainabilityGoal.objects.filter(department=department)
    total_goals = goals.count()
    if total_goals:
        achieved = goals.filter(status=SustainabilityGoal.Status.ACHIEVED).count()
        active = goals.filter(status=SustainabilityGoal.Status.ACTIVE).count()
        goal_score = (Decimal(achieved) + Decimal(active) * Decimal("0.5")) / total_goals * HUNDRED
    else:
        goal_score = NEUTRAL

    # Relative emission performance: greenest department scores highest.
    if max_department_co2e is None:
        max_department_co2e = (
            Department.objects.order_by("-total_co2e_kg")
            .values_list("total_co2e_kg", flat=True)
            .first()
            or ZERO
        )
    max_department_co2e = Decimal(str(max_department_co2e))
    dept_co2e = Decimal(str(department.total_co2e_kg or 0))
    if max_department_co2e > 0:
        emission_score = (HUNDRED - (dept_co2e / max_department_co2e * HUNDRED))
    else:
        emission_score = HUNDRED  # nobody has emitted anything yet

    return _q(goal_score * Decimal("0.5") + emission_score * Decimal("0.5"))


def social_score(department) -> Decimal:
    from apps.core.v1.enums import ApprovalStatus
    from apps.engagement.v1.models import ChallengeParticipation
    from apps.social_impact.v1.models import EmployeeParticipation

    member_count = department.members.count()
    if not member_count:
        return NEUTRAL

    csr = EmployeeParticipation.objects.filter(
        employee__department=department, status=ApprovalStatus.APPROVED
    ).count()
    challenges = ChallengeParticipation.objects.filter(
        employee__department=department, status=ApprovalStatus.APPROVED
    ).count()

    # Approved contributions per member, capped so 1 approved item/member == 100.
    rate = (Decimal(csr + challenges) / Decimal(member_count)) * HUNDRED
    return _q(rate)


def governance_score(department) -> Decimal:
    from apps.compliance.v1.models import (
        ComplianceIssue,
        ESGPolicy,
        PolicyAcknowledgement,
    )

    member_count = department.members.count()
    active_policies = ESGPolicy.objects.filter(is_active=True).count()
    expected_acks = member_count * active_policies
    if expected_acks:
        done = PolicyAcknowledgement.objects.filter(
            employee__department=department, acknowledged_at__isnull=False
        ).count()
        ack_rate = Decimal(min(done, expected_acks)) / Decimal(expected_acks) * HUNDRED
    else:
        ack_rate = NEUTRAL

    # Compliance health: penalise open and (more heavily) overdue issues on this
    # department's audits.
    today = timezone.now().date()
    dept_issues = ComplianceIssue.objects.filter(audit__department=department)
    open_issues = dept_issues.exclude(status=ComplianceIssue.Status.RESOLVED)
    overdue = open_issues.filter(due_date__lt=today).count()
    open_count = open_issues.count()
    compliance_health = HUNDRED - (Decimal(overdue) * 20 + Decimal(open_count) * 5)

    return _q(ack_rate * Decimal("0.5") + _q(compliance_health) * Decimal("0.5"))


# --------------------------------------------------------------------------- #
# Aggregation
# --------------------------------------------------------------------------- #
def _weights():
    from apps.system_core.v1.models import GlobalConfiguration

    cfg = GlobalConfiguration.load()
    we, ws, wg = (
        Decimal(cfg.weight_environmental),
        Decimal(cfg.weight_social),
        Decimal(cfg.weight_governance),
    )
    total = we + ws + wg
    if total == 0:  # guard against misconfiguration
        we = ws = wg = Decimal(1)
        total = Decimal(3)
    return we, ws, wg, total


def compute_department_score(department, *, period_year=None, max_department_co2e=None,
                             persist=True):
    """Compute all three pillars + total for one department.

    Returns a dict; when ``persist`` is True, upserts a DepartmentScore row and
    updates ``Department.esg_score`` with the total.
    """
    from .models import Department, DepartmentScore

    if period_year is None:
        from apps.system_core.v1.models import GlobalConfiguration

        period_year = GlobalConfiguration.load().current_reporting_year

    env = environmental_score(department, max_department_co2e=max_department_co2e)
    soc = social_score(department)
    gov = governance_score(department)

    we, ws, wg, total_w = _weights()
    total = _q((env * we + soc * ws + gov * wg) / total_w)

    if persist:
        DepartmentScore.objects.update_or_create(
            department=department,
            period_year=period_year,
            defaults={
                "environmental_score": env,
                "social_score": soc,
                "governance_score": gov,
                "total_score": total,
            },
        )
        Department.all_objects.filter(pk=department.pk).update(esg_score=total)

    return {
        "department": department,
        "period_year": period_year,
        "environmental_score": env,
        "social_score": soc,
        "governance_score": gov,
        "total_score": total,
    }


def recompute_all(*, period_year=None, persist=True):
    """Recompute scores for every active department. Returns a list of dicts."""
    from .models import Department

    departments = list(Department.objects.filter(is_active=True))
    max_co2e = max((Decimal(str(d.total_co2e_kg or 0)) for d in departments), default=ZERO)

    return [
        compute_department_score(
            dept, period_year=period_year, max_department_co2e=max_co2e, persist=persist
        )
        for dept in departments
    ]


def overall_esg_score(*, period_year=None, recompute=False) -> Decimal:
    """Organization-wide score = mean of department Total scores."""
    from .models import DepartmentScore

    if recompute:
        rows = recompute_all(period_year=period_year)
        totals = [r["total_score"] for r in rows]
    else:
        qs = DepartmentScore.objects.all()
        if period_year is not None:
            qs = qs.filter(period_year=period_year)
        totals = [s.total_score for s in qs]

    if not totals:
        return ZERO
    return _q(sum(totals) / Decimal(len(totals)))
