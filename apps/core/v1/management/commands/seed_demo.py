"""Populate the database with realistic demo data for every module.

    python manage.py seed_demo

Idempotent (safe to re-run). Runs under rls_admin() so it can write across all
departments. All screens read this data back through the RLS-scoped APIs — there
is no hard-coded data in the templates or JS.
"""
import datetime as dt
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.core.v1.enums import ApprovalStatus, MeasurementUnit, SourceType
from apps.core.v1.rls.context import rls_admin

User = get_user_model()


class Command(BaseCommand):
    help = "Seed demo data (departments, users, ERP records, ESG, gamification)."

    def handle(self, *args, **options):
        with rls_admin():
            self._seed()
        self.stdout.write(self.style.SUCCESS("Demo data seeded. All pages now read it via the APIs."))

    def _seed(self):
        from apps.compliance.v1.models import Audit, ComplianceIssue, ESGPolicy, PolicyAcknowledgement
        from apps.engagement.v1.models import Badge, BadgeUnlockRule, Challenge, EmployeeProfile, Reward
        from apps.environmental.v1.models import Department, EmissionFactor, SustainabilityGoal
        from apps.environmental.v1.scoring import recompute_all
        from apps.fleet_ops.v1.models import FleetLog, Vehicle
        from apps.manufacturing.v1.models import ProductionOrder, ResourceUsage
        from apps.notifications.v1.models import Notification
        from apps.procurement.v1.models import PurchaseOrder, Vendor
        from apps.social_impact.v1.models import CSRActivity, EmployeeParticipation
        from apps.system_core.v1.models import Category, GlobalConfiguration, ProductESGProfile

        today = timezone.now().date()
        GlobalConfiguration.load()  # ensure the singleton exists

        # ── Departments ──
        dept_specs = [("Operations", "OPS"), ("Logistics", "LOG"),
                      ("Manufacturing", "MFG"), ("Corporate", "CORP"), ("R&D", "RND")]
        depts = {}
        for name, code in dept_specs:
            depts[code], _ = Department.objects.get_or_create(code=code, defaults={"name": name})

        # ── Users (one manager per dept + a few employees) ──
        def make_user(username, name, role, code, xp=0):
            u, created = User.objects.get_or_create(
                username=username,
                defaults=dict(email=f"{username}@ecosphere.test", first_name=name,
                              role=role, department=depts[code]),
            )
            if created:
                u.set_password("Demo!2345")
                u.save()
            profile, _ = EmployeeProfile.objects.get_or_create(user=u)
            if xp:
                profile.xp_balance = xp
                profile.total_earned_xp = max(profile.total_earned_xp, xp)
                profile.save()
            return u

        demo = make_user("demo", "Demo", "MANAGER", "OPS", xp=350)
        make_user("ravi", "Ravi", "MANAGER", "MFG", xp=430)
        employees = [
            make_user("aditi", "Aditi", "EMPLOYEE", "OPS", xp=520),
            make_user("karan", "Karan", "EMPLOYEE", "OPS", xp=280),
            make_user("priya", "Priya", "EMPLOYEE", "OPS", xp=610),
            make_user("neha", "Neha", "EMPLOYEE", "MFG", xp=340),
            make_user("arjun", "Arjun", "EMPLOYEE", "LOG", xp=190),
        ]

        # ── Master data ──
        for name, sku, kg, rec, ethics in [
            ("Recycled Notebook", "SKU-NB-01", "0.5", True, 82),
            ("Steel Water Bottle", "SKU-WB-02", "1.2", True, 90),
            ("Plastic Casing", "SKU-PC-03", "3.4", False, 45),
        ]:
            ProductESGProfile.objects.get_or_create(sku=sku, defaults=dict(
                name=name, carbon_footprint_kg=Decimal(kg), recyclable=rec,
                ethical_sourcing_score=ethics))
        for cname, ctype in [("Environment", "CSR_ACTIVITY"), ("Community", "CSR_ACTIVITY"),
                             ("Wellness", "CHALLENGE"), ("Energy", "CHALLENGE")]:
            Category.objects.get_or_create(name=cname, type=ctype)

        # ── Emission factors ──
        factors = {
            SourceType.DIESEL: "2.68", SourceType.PETROL: "2.31",
            SourceType.ELECTRICITY: "0.82", SourceType.WATER: "0.34",
        }
        for src, val in factors.items():
            EmissionFactor.objects.get_or_create(
                source_type=src, is_active=True,
                defaults=dict(name=src.label, unit=MeasurementUnit.LITER,
                              factor_value=Decimal(val), effective_from=today))

        # ── ERP records -> carbon transactions via signals ──
        truck, _ = Vehicle.objects.get_or_create(
            registration_no="OPS-TRUCK-1",
            defaults=dict(name="Ops Truck", vehicle_type="TRUCK",
                          fuel_type=SourceType.DIESEL, department=depts["OPS"]))
        if not FleetLog.objects.filter(vehicle=truck).exists():
            for i, litres in enumerate([40, 55, 70, 65, 50, 35, 45, 60, 80, 70, 55, 48]):
                d = today.replace(day=15) - dt.timedelta(days=30 * (11 - i))
                FleetLog.objects.create(vehicle=truck, log_date=d,
                                        fuel_quantity=Decimal(litres), logged_by=demo)

        vendor, _ = Vendor.objects.get_or_create(name="GreenPower Utilities")
        PurchaseOrder.objects.get_or_create(
            reference="PO-EL-1001",
            defaults=dict(vendor=vendor, department=depts["CORP"],
                          item_type=PurchaseOrder.ItemType.ELECTRICITY, quantity=Decimal("1200"),
                          unit=MeasurementUnit.KWH, amount=Decimal("9600"),
                          order_date=today - dt.timedelta(days=10), created_by=demo))

        prod, _ = ProductionOrder.objects.get_or_create(
            reference="MO-2001",
            defaults=dict(product_name="Widget A", department=depts["MFG"],
                          quantity_produced=Decimal("500"), production_date=today - dt.timedelta(days=5),
                          status=ProductionOrder.Status.COMPLETED))
        if not ResourceUsage.objects.filter(production_order=prod).exists():
            ResourceUsage.objects.create(production_order=prod,
                                         resource_type=ResourceUsage.ResourceType.ELECTRICITY,
                                         quantity=Decimal("800"), unit=MeasurementUnit.KWH,
                                         waste_generated_kg=Decimal("40"))

        # ── Environmental goals ──
        for title, code, metric, base, tgt in [
            ("Reduce Fleet Emissions", "OPS", SustainabilityGoal.Metric.CARBON_REDUCTION, 100, 90),
            ("Cut Packaging Waste", "MFG", SustainabilityGoal.Metric.WASTE_REDUCTION, 120, 100),
            ("Office Energy Cut", "CORP", SustainabilityGoal.Metric.ENERGY_REDUCTION, 80, 68),
        ]:
            SustainabilityGoal.objects.get_or_create(
                department=depts[code], title=title,
                defaults=dict(metric=metric, baseline_value=base, target_value=tgt,
                              target_date=today + dt.timedelta(days=180)))

        # ── Social: CSR activities + participation queue ──
        acts = {}
        for title, cat, xp in [("Tree Plantation", "ENVIRONMENT", 100),
                               ("Blood Donation", "HEALTH", 80),
                               ("Beach Cleanup", "ENVIRONMENT", 120)]:
            acts[title], _ = CSRActivity.objects.get_or_create(
                title=title, defaults=dict(category=cat, xp_reward=xp,
                    start_date=today, end_date=today + dt.timedelta(days=30)))
        EmployeeParticipation.objects.get_or_create(
            activity=acts["Tree Plantation"], employee=employees[0],
            defaults=dict(status=ApprovalStatus.PENDING))
        EmployeeParticipation.objects.get_or_create(
            activity=acts["Beach Cleanup"], employee=employees[1],
            defaults=dict(status=ApprovalStatus.PENDING))

        # ── Governance: policies, acks, audits, issues ──
        policies = {}
        for title, pillar in [("Anti-Corruption Policy", "G"), ("Environmental Policy", "E"),
                              ("Code of Conduct", "S")]:
            policies[title], _ = ESGPolicy.objects.get_or_create(
                title=title, defaults=dict(pillar=pillar, version="1.0", effective_date=today))
        for u in [demo] + employees:
            PolicyAcknowledgement.objects.get_or_create(
                policy=policies["Anti-Corruption Policy"], employee=u)

        audit, _ = Audit.objects.get_or_create(
            title="Q3 Internal Audit", department=depts["OPS"],
            defaults=dict(audit_type=Audit.AuditType.INTERNAL, scheduled_date=today, auditor=demo))
        ComplianceIssue.objects.get_or_create(
            audit=audit, title="Missing emissions filing",
            defaults=dict(owner=demo, due_date=today - dt.timedelta(days=2),
                          severity="HIGH", status=ComplianceIssue.Status.OPEN))
        ComplianceIssue.objects.get_or_create(
            audit=audit, title="Untracked waste disposal",
            defaults=dict(owner=employees[0], due_date=today + dt.timedelta(days=14),
                          severity="MEDIUM", status=ComplianceIssue.Status.IN_PROGRESS))

        # ── Gamification: challenges, badges, rewards ──
        for title, diff, xp in [("Zero Waste Week", "MEDIUM", 150),
                                ("Cycle to Work", "EASY", 80),
                                ("Energy Saver Sprint", "HARD", 250)]:
            Challenge.objects.get_or_create(
                title=title, defaults=dict(difficulty=diff, xp_reward=xp,
                    start_date=today, end_date=today + dt.timedelta(days=21),
                    deadline=today + dt.timedelta(days=21), status=Challenge.Status.ACTIVE))
        for name, tier, xp, icon in [("Eco Starter", "BRONZE", 100, "🌱"),
                                     ("Green Warrior", "SILVER", 500, "🌿"),
                                     ("Sustainability Champion", "GOLD", 1000, "🏆")]:
            b, _ = Badge.objects.get_or_create(name=name, defaults=dict(tier=tier, icon=icon))
            BadgeUnlockRule.objects.get_or_create(badge=b, defaults=dict(min_total_xp=xp))
        for name, desc, pts, stock in [("Eco Water Bottle", "Reusable steel bottle", 100, 25),
                                       ("Coffee Mug", "EcoSphere branded mug", 150, 10),
                                       ("Extra Day Off", "One paid day off", 800, 3)]:
            Reward.objects.get_or_create(name=name, defaults=dict(
                description=desc, points_required=pts, stock_count=stock))

        # ── Notifications for the demo user ──
        for title, cat in [("42 new Carbon Transactions logged", "SYSTEM"),
                           ("New compliance issue in Operations", "COMPLIANCE"),
                           ("You earned 100 XP", "GAMIFICATION")]:
            Notification.objects.get_or_create(recipient=demo, title=title, defaults=dict(category=cat))

        # ── Scores (feeds the dashboard + reports) ──
        recompute_all()
        self.stdout.write(self.style.SUCCESS("  scores recomputed"))
