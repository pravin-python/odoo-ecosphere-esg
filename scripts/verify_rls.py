"""End-to-end RLS proof. Run against a Postgres DB that has had:
    python manage.py migrate && python manage.py setup_rls

    python manage.py shell < scripts/verify_rls.py

Sets up two departments and asserts that each role sees only the rows RLS
permits. Exits non-zero on any failure.
"""
import datetime as dt

from django.contrib.auth import get_user_model
from django.db import connection

from apps.core.v1.enums import MeasurementUnit, SourceType
from apps.core.v1.rls.context import apply_user_context, clear_context, rls_admin
from apps.environmental.v1.models import CarbonTransaction, Department, EmissionFactor
from apps.notifications.v1.models import Notification

User = get_user_model()
today = dt.date.today()

assert connection.vendor == "postgresql", "verify_rls requires PostgreSQL"

failures = []


def check(label, got, expected):
    ok = got == expected
    print(f"[{'OK ' if ok else 'FAIL'}] {label}: got {got}, expected {expected}")
    if not ok:
        failures.append(label)


# ── Seed data (bypass RLS so WITH CHECK doesn't block cross-dept setup) ──
with rls_admin():
    User.objects.filter(username__startswith="rls_").delete()
    Department.objects.filter(code__in=["RLSA", "RLSB"]).delete()

    dept_a = Department.objects.create(name="RLS Dept A", code="RLSA")
    dept_b = Department.objects.create(name="RLS Dept B", code="RLSB")

    mgr_a = User.objects.create_user("rls_mgr_a", email="rls_mgr_a@x.com", password="pw",
                                     role="MANAGER", department=dept_a)
    emp_a = User.objects.create_user("rls_emp_a", email="rls_emp_a@x.com", password="pw",
                                     role="EMPLOYEE", department=dept_a)
    mgr_b = User.objects.create_user("rls_mgr_b", email="rls_mgr_b@x.com", password="pw",
                                     role="MANAGER", department=dept_b)
    boss = User.objects.create_user("rls_admin", email="rls_admin@x.com", password="pw",
                                    role="ADMIN")

    factor = EmissionFactor.objects.create(
        name="Diesel", source_type=SourceType.DIESEL, unit=MeasurementUnit.LITER,
        factor_value="2.68", effective_from=today,
    )

    def make_txn(dept, qty):
        return CarbonTransaction.objects.create(
            department=dept, source_type=SourceType.DIESEL, emission_factor=factor,
            quantity=qty, co2e_kg=qty, occurred_on=today,
        )

    make_txn(dept_a, 10)
    make_txn(dept_a, 20)
    make_txn(dept_b, 30)

    Notification.objects.create(recipient=emp_a, title="For emp A")
    Notification.objects.create(recipient=mgr_b, title="For mgr B")

# ── Assertions per role context ──
try:
    apply_user_context(mgr_a)
    check("Manager A sees only Dept A carbon rows",
          CarbonTransaction.objects.count(), 2)

    apply_user_context(mgr_b)
    check("Manager B sees only Dept B carbon rows",
          CarbonTransaction.objects.count(), 1)

    apply_user_context(emp_a)
    check("Employee A sees Dept A carbon rows (department-shared)",
          CarbonTransaction.objects.count(), 2)
    check("Employee A sees only their own notification",
          Notification.objects.count(), 1)

    apply_user_context(mgr_b)
    check("Manager B cannot see Employee A's notification",
          Notification.objects.filter(title="For emp A").count(), 0)

    apply_user_context(boss)
    check("Admin sees all carbon rows across departments",
          CarbonTransaction.objects.count(), 3)

    clear_context()
    check("Anonymous/no-context sees zero rows (fail closed)",
          CarbonTransaction.objects.count(), 0)
finally:
    clear_context()

print()
if failures:
    print(f"RLS VERIFICATION FAILED: {failures}")
    raise SystemExit(1)
print("ALL RLS CHECKS PASSED")
