from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.core.v1.enums import ApprovalStatus
from apps.engagement.v1.models import Challenge, ChallengeParticipation, EmployeeProfile

User = get_user_model()


class ChallengeParticipationSignalTests(TestCase):
    def setUp(self):
        self.emp = User.objects.create_user(username="p1", email="p1@x.com", password="x")
        self.challenge = Challenge.objects.create(
            title="Zero Waste Week", xp_reward=120,
            start_date=date(2026, 1, 1), end_date=date(2026, 1, 8),
            status=Challenge.Status.ACTIVE,
        )

    def test_no_xp_while_pending(self):
        ChallengeParticipation.objects.create(challenge=self.challenge, employee=self.emp)
        profile = EmployeeProfile.objects.get(user=self.emp)
        self.assertEqual(profile.total_earned_xp, 0)

    def test_xp_awarded_once_on_approval(self):
        part = ChallengeParticipation.objects.create(
            challenge=self.challenge, employee=self.emp
        )
        part.status = ApprovalStatus.APPROVED
        part.save()

        profile = EmployeeProfile.objects.get(user=self.emp)
        self.assertEqual(profile.total_earned_xp, 120)

        # Saving again must not double-award.
        part.refresh_from_db()
        part.save()
        profile.refresh_from_db()
        self.assertEqual(profile.total_earned_xp, 120)

    def test_challenge_lifecycle_default_is_draft(self):
        c = Challenge.objects.create(
            title="Draft one", start_date=date(2026, 2, 1), end_date=date(2026, 2, 2)
        )
        self.assertEqual(c.status, Challenge.Status.DRAFT)
