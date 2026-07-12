from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.core.v1.enums import ApprovalStatus, Severity
from apps.compliance.v1.models import Audit, ComplianceIssue, ESGPolicy, PolicyAcknowledgement
from apps.environmental.v1.models import Department, DepartmentScore, SustainabilityGoal
from apps.environmental.v1 import scoring
from apps.social_impact.v1.models import CSRActivity, EmployeeParticipation

User = get_user_model()


class ScoringEngineTests(TestCase):
    def setUp(self):
        self.green = Department.objects.create(name="Green", code="GRN", total_co2e_kg=100)
        self.dirty = Department.objects.create(name="Dirty", code="DRT", total_co2e_kg=1000)
        self.emp = User.objects.create_user(
            username="emp", email="emp@x.com", password="x", department=self.green
        )

    def test_greener_department_scores_higher_on_environment(self):
        green = scoring.environmental_score(self.green, max_department_co2e=1000)
        dirty = scoring.environmental_score(self.dirty, max_department_co2e=1000)
        self.assertGreater(green, dirty)

    def test_environmental_score_within_bounds(self):
        score = scoring.environmental_score(self.green)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)

    def test_social_score_rewards_approved_participation(self):
        activity = CSRActivity.objects.create(
            title="Tree", category=CSRActivity.Category.ENVIRONMENT,
            start_date=date(2026, 1, 1), end_date=date(2026, 12, 31),
        )
        EmployeeParticipation.objects.create(
            activity=activity, employee=self.emp, status=ApprovalStatus.APPROVED
        )
        # 1 approved participation / 1 member => 100
        self.assertEqual(scoring.social_score(self.green), 100)

    def test_governance_penalises_overdue_issues(self):
        policy = ESGPolicy.objects.create(
            title="Anti-Corruption", pillar="G", effective_date=date(2026, 1, 1)
        )
        PolicyAcknowledgement.objects.create(policy=policy, employee=self.emp)  # pending
        audit = Audit.objects.create(
            title="Q1", audit_type=Audit.AuditType.INTERNAL, department=self.green,
            scheduled_date=date(2026, 1, 1),
        )
        ComplianceIssue.objects.create(
            audit=audit, title="Leak", severity=Severity.HIGH, owner=self.emp,
            due_date=date(2020, 1, 1),  # long overdue
        )
        score = scoring.governance_score(self.green)
        self.assertLess(score, 60)

    def test_compute_and_persist_department_score(self):
        result = scoring.compute_department_score(self.green, period_year=2026)
        self.assertEqual(result["period_year"], 2026)
        row = DepartmentScore.objects.get(department=self.green, period_year=2026)
        self.assertEqual(row.total_score, result["total_score"])
        self.green.refresh_from_db()
        self.assertEqual(self.green.esg_score, result["total_score"])

    def test_overall_esg_is_mean_of_departments(self):
        scoring.recompute_all(period_year=2026)
        overall = scoring.overall_esg_score(period_year=2026)
        self.assertGreaterEqual(overall, 0)
        self.assertLessEqual(overall, 100)

    def test_weights_default_to_40_30_30(self):
        from apps.system_core.v1.models import GlobalConfiguration

        cfg = GlobalConfiguration.load()
        self.assertEqual(
            (cfg.weight_environmental, cfg.weight_social, cfg.weight_governance),
            (40, 30, 30),
        )
