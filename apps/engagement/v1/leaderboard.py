"""Leaderboard queries for the gamification module.

Read-only helpers used by dashboards/reports. Kept separate from ``services.py``
(which mutates XP/rewards) so ranking logic stays easy to reason about.
"""


def employee_leaderboard(*, limit=10, department=None):
    """Top employees by lifetime XP. Optionally scoped to one department.

    Returns a list of dicts: rank, name, department, total_xp, level, badges.
    """
    from .models import EmployeeProfile

    qs = EmployeeProfile.objects.select_related("user", "user__department")
    if department is not None:
        qs = qs.filter(user__department=department)
    qs = qs.order_by("-total_earned_xp", "user__username")[:limit]

    rows = []
    for rank, p in enumerate(qs, start=1):
        rows.append({
            "rank": rank,
            "name": p.user.get_full_name() or p.user.username,
            "department": p.user.department.name if p.user.department else "—",
            "total_xp": p.total_earned_xp,
            "level": p.level,
            "badges": p.badges.count(),
        })
    return rows


def department_leaderboard(*, period_year=None, limit=None):
    """Departments ranked by their latest ESG Total score.

    Returns a list of dicts: rank, department, environmental, social,
    governance, total.
    """
    from apps.environmental.v1.models import DepartmentScore

    qs = DepartmentScore.objects.select_related("department")
    if period_year is not None:
        qs = qs.filter(period_year=period_year)
    qs = qs.order_by("-total_score")
    if limit:
        qs = qs[:limit]

    rows = []
    for rank, s in enumerate(qs, start=1):
        rows.append({
            "rank": rank,
            "department": s.department.name,
            "environmental": float(s.environmental_score),
            "social": float(s.social_score),
            "governance": float(s.governance_score),
            "total": float(s.total_score),
        })
    return rows
