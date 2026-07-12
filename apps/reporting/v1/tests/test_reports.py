from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.core.v1.enums import Severity
from apps.compliance.v1.models import Audit, ComplianceIssue
from apps.environmental.v1.models import Department
from apps.reporting.v1 import exporters, services

User = get_user_model()


class ReportBuilderTests(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(name="Ops", code="OPS")
        self.owner = User.objects.create_user(username="o", email="o@x.com", password="x")
        audit = Audit.objects.create(
            title="A1", audit_type=Audit.AuditType.INTERNAL, department=self.dept,
            scheduled_date=date(2026, 1, 1),
        )
        ComplianceIssue.objects.create(
            audit=audit, title="Missing log", severity=Severity.MEDIUM, owner=self.owner,
            due_date=date(2026, 6, 1),
        )

    def test_governance_report_has_rows_and_summary(self):
        result = services.build_report("GOVERNANCE")
        self.assertEqual(len(result.rows), 1)
        self.assertIn("Total issues", result.summary)
        self.assertEqual(result.rows[0]["Issue"], "Missing log")

    def test_department_filter_applies(self):
        other = Department.objects.create(name="HR", code="HR")
        result = services.build_report("GOVERNANCE", {"department": other.id})
        self.assertEqual(len(result.rows), 0)

    def test_unknown_report_type_raises(self):
        with self.assertRaises(ValueError):
            services.build_report("NONSENSE")

    def test_csv_export(self):
        result = services.build_report("GOVERNANCE")
        payload, content_type, filename = exporters.export_report(result, "csv")
        self.assertIsInstance(payload, bytes)
        self.assertEqual(content_type, "text/csv")
        self.assertTrue(filename.endswith(".csv"))
        self.assertIn(b"Missing log", payload)

    def test_xlsx_export(self):
        result = services.build_report("GOVERNANCE")
        payload, content_type, _ = exporters.export_report(result, "xlsx")
        # XLSX is a zip archive — starts with the PK signature.
        self.assertTrue(payload.startswith(b"PK"))

    def test_pdf_export(self):
        result = services.build_report("GOVERNANCE")
        payload, content_type, _ = exporters.export_report(result, "pdf")
        self.assertTrue(payload.startswith(b"%PDF"))

    def test_esg_summary_runs_with_no_scores(self):
        result = services.build_report("ESG_SUMMARY")
        self.assertIn("Overall ESG Score", result.summary)
