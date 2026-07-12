"""Declarative row-level-security policy registry.

Each rule maps a Django model to a visibility *scope*. The ``setup_rls``
command resolves models to their real table/column names and generates the
Postgres policy SQL — so table names are never hard-coded and stay correct as
models evolve.

Adjust the RBAC matrix here (one place), then re-run ``manage.py setup_rls``.

Privileged roles (see the full table regardless of scope) default to ADMIN and
GOVERNANCE_OFFICER — both need org-wide oversight for ESG scoring/reporting.
The ``accounts_v1.User`` table is deliberately excluded to avoid an auth
bootstrap deadlock.
"""
from dataclasses import dataclass, field

# Scope kinds
DEPARTMENT = "department"                 # row has a direct department FK
DEPARTMENT_VIA = "department_via"         # department reached through a FK join
SELF_DEPARTMENT = "self_department"       # the Department row itself
OWNER = "owner"                           # personal row, visible only to its owner
OWNER_OR_DEPT_MANAGER = "owner_or_dept_manager"  # owner + that owner's dept manager
OWNER_OR_DEPARTMENT_VIA = "owner_or_department_via"  # owner + anyone in the row's dept

PRIVILEGED_DEFAULT = ("ADMIN", "GOVERNANCE_OFFICER")


@dataclass(frozen=True)
class RLSRule:
    model: str                      # "app_label.ModelName"
    scope: str
    column: str = ""                # scope column (e.g. "department_id", "recipient_id")
    ref_model: str = ""             # for *_VIA scopes: the joined model
    ref_column: str = "department_id"
    privileged_roles: tuple = field(default=PRIVILEGED_DEFAULT)


# ── The RBAC matrix ──────────────────────────────────────────────────────────
RLS_RULES = [
    # The organizational unit itself: members see their own department.
    RLSRule("environmental_v1.Department", SELF_DEPARTMENT),

    # Department-scoped operational data (direct department_id column).
    RLSRule("environmental_v1.CarbonTransaction", DEPARTMENT, column="department_id"),
    RLSRule("fleet_ops_v1.Vehicle", DEPARTMENT, column="department_id"),
    RLSRule("procurement_v1.PurchaseOrder", DEPARTMENT, column="department_id"),
    RLSRule("manufacturing_v1.ProductionOrder", DEPARTMENT, column="department_id"),
    RLSRule("compliance_v1.Audit", DEPARTMENT, column="department_id"),

    # Department reached through a foreign key (no direct department column).
    RLSRule("fleet_ops_v1.FleetLog", DEPARTMENT_VIA,
            column="vehicle_id", ref_model="fleet_ops_v1.Vehicle"),
    RLSRule("manufacturing_v1.ResourceUsage", DEPARTMENT_VIA,
            column="production_order_id", ref_model="manufacturing_v1.ProductionOrder"),

    # Compliance issues: the owner, plus anyone in the audit's department.
    RLSRule("compliance_v1.ComplianceIssue", OWNER_OR_DEPARTMENT_VIA,
            column="owner_id", ref_model="compliance_v1.Audit", ref_column="audit_id"),

    # Personal rows — visible only to their owner (or a privileged role).
    RLSRule("notifications_v1.Notification", OWNER, column="recipient_id"),
    RLSRule("engagement_v1.EmployeeProfile", OWNER, column="user_id"),

    # CSR / policy: the employee who owns it, plus their department manager.
    RLSRule("social_impact_v1.EmployeeParticipation", OWNER_OR_DEPT_MANAGER, column="employee_id"),
    RLSRule("compliance_v1.PolicyAcknowledgement", OWNER_OR_DEPT_MANAGER, column="employee_id"),
]
