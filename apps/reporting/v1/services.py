"""Report dataset builders.

Each builder returns a :class:`ReportResult` (title + column headers + row dicts)
that the exporters in ``exporters.py`` can render to CSV / XLSX / PDF. Filters are
a plain dict so the same set works for the Custom Report Builder and for saved
reports:

    {
        "department": <id>, "date_from": "2026-01-01", "date_to": "2026-12-31",
        "employee": <id>, "challenge": <id>, "esg_category": "E"|"S"|"G",
    }
"""
from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass
class ReportResult:
    title: str
    columns: list[str]
    rows: list[dict[str, Any]] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)


def _parse_date(value):
    if not value or isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _apply_date_range(qs, field_name, filters):
    df, dt = _parse_date(filters.get("date_from")), _parse_date(filters.get("date_to"))
    if df:
        qs = qs.filter(**{f"{field_name}__gte": df})
    if dt:
        qs = qs.filter(**{f"{field_name}__lte": dt})
    return qs


# --------------------------------------------------------------------------- #
# Environmental
# --------------------------------------------------------------------------- #
def environmental_report(filters=None) -> ReportResult:
    from apps.environmental.v1.models import CarbonTransaction

    filters = filters or {}
    qs = CarbonTransaction.objects.select_related("department", "emission_factor")
    if filters.get("department"):
        qs = qs.filter(department_id=filters["department"])
    if filters.get("module"):
        qs = qs.filter(source_type=filters["module"])
    qs = _apply_date_range(qs, "occurred_on", filters)

    rows, total = [], 0
    for t in qs:
        total += float(t.co2e_kg)
        rows.append({
            "Date": t.occurred_on.isoformat(),
            "Department": t.department.name,
            "Source": t.get_source_type_display(),
            "Quantity": float(t.quantity),
            "CO2e (kg)": float(t.co2e_kg),
        })
    return ReportResult(
        title="Environmental Report — Carbon Transactions",
        columns=["Date", "Department", "Source", "Quantity", "CO2e (kg)"],
        rows=rows,
        summary={"Total transactions": len(rows), "Total CO2e (kg)": round(total, 3)},
    )


# --------------------------------------------------------------------------- #
# Social
# --------------------------------------------------------------------------- #
def social_report(filters=None) -> ReportResult:
    from apps.social_impact.v1.models import EmployeeParticipation

    filters = filters or {}
    qs = EmployeeParticipation.objects.select_related("activity", "employee")
    if filters.get("department"):
        qs = qs.filter(employee__department_id=filters["department"])
    if filters.get("employee"):
        qs = qs.filter(employee_id=filters["employee"])
    qs = _apply_date_range(qs, "created_at__date", filters)

    rows = []
    for p in qs:
        rows.append({
            "Employee": p.employee.get_full_name() or p.employee.username,
            "Activity": p.activity.title,
            "Category": p.activity.get_category_display(),
            "Status": p.get_status_display(),
            "XP Awarded": p.activity.xp_reward if p.xp_awarded else 0,
            "Submitted": p.created_at.date().isoformat(),
        })
    approved = sum(1 for r in rows if r["Status"] == "Approved")
    return ReportResult(
        title="Social Report — CSR Participation",
        columns=["Employee", "Activity", "Category", "Status", "XP Awarded", "Submitted"],
        rows=rows,
        summary={"Total submissions": len(rows), "Approved": approved},
    )


# --------------------------------------------------------------------------- #
# Governance
# --------------------------------------------------------------------------- #
def governance_report(filters=None) -> ReportResult:
    from django.utils import timezone

    from apps.compliance.v1.models import ComplianceIssue

    filters = filters or {}
    qs = ComplianceIssue.objects.select_related("audit", "audit__department", "owner")
    if filters.get("department"):
        qs = qs.filter(audit__department_id=filters["department"])
    qs = _apply_date_range(qs, "due_date", filters)

    today = timezone.now().date()
    rows, overdue = [], 0
    for i in qs:
        is_overdue = i.status != ComplianceIssue.Status.RESOLVED and i.due_date < today
        overdue += int(is_overdue)
        rows.append({
            "Issue": i.title,
            "Department": i.audit.department.name,
            "Severity": i.get_severity_display(),
            "Owner": i.owner.get_full_name() or i.owner.username,
            "Due Date": i.due_date.isoformat(),
            "Status": i.get_status_display(),
            "Overdue": "Yes" if is_overdue else "No",
        })
    return ReportResult(
        title="Governance Report — Compliance Issues",
        columns=["Issue", "Department", "Severity", "Owner", "Due Date", "Status", "Overdue"],
        rows=rows,
        summary={"Total issues": len(rows), "Overdue": overdue},
    )


# --------------------------------------------------------------------------- #
# ESG Summary
# --------------------------------------------------------------------------- #
def esg_summary_report(filters=None) -> ReportResult:
    from apps.environmental.v1.models import DepartmentScore
    from apps.environmental.v1.scoring import overall_esg_score

    filters = filters or {}
    qs = DepartmentScore.objects.select_related("department")
    if filters.get("department"):
        qs = qs.filter(department_id=filters["department"])
    if filters.get("period_year"):
        qs = qs.filter(period_year=filters["period_year"])

    rows = []
    for s in qs:
        rows.append({
            "Department": s.department.name,
            "Year": s.period_year,
            "Environmental": float(s.environmental_score),
            "Social": float(s.social_score),
            "Governance": float(s.governance_score),
            "Total": float(s.total_score),
        })
    overall = float(overall_esg_score(period_year=filters.get("period_year")))
    return ReportResult(
        title="ESG Summary Report",
        columns=["Department", "Year", "Environmental", "Social", "Governance", "Total"],
        rows=rows,
        summary={"Departments scored": len(rows), "Overall ESG Score": overall},
    )


REPORT_BUILDERS = {
    "ENVIRONMENTAL": environmental_report,
    "SOCIAL": social_report,
    "GOVERNANCE": governance_report,
    "ESG_SUMMARY": esg_summary_report,
}


def build_report(report_type: str, filters=None) -> ReportResult:
    """Custom Report Builder entry point — dispatch by report type."""
    try:
        builder = REPORT_BUILDERS[report_type]
    except KeyError:
        raise ValueError(f"Unknown report type: {report_type!r}")
    return builder(filters or {})
