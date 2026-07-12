"""Assembles the versioned REST API surface (/api/v1/...) from every module.

One place to see the whole API; each app owns its serializers/viewsets in its
own ``v1/api.py``.
"""
from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.compliance.v1 import api as gov_api
from apps.engagement.v1 import api as gam_api
from apps.engagement.v1.api import LeaderboardView, MyProfileView
from apps.environmental.v1 import api as env_api
from apps.notifications.v1 import api as notif_api
from apps.reporting.v1.api import ReportExportView
from apps.social_impact.v1 import api as soc_api
from apps.system_core.v1 import api as sys_api

router = DefaultRouter()

# Environmental
router.register("environmental/emission-factors", env_api.EmissionFactorViewSet, "emission-factors")
router.register("environmental/carbon", env_api.CarbonTransactionViewSet, "carbon")
router.register("environmental/goals", env_api.SustainabilityGoalViewSet, "goals")

# Master data (Environmental products + Settings)
router.register("catalog/departments", env_api.DepartmentViewSet, "departments")
router.register("catalog/products", sys_api.ProductESGProfileViewSet, "products")
router.register("catalog/categories", sys_api.CategoryViewSet, "categories")

# Social
router.register("social/activities", soc_api.CSRActivityViewSet, "csr-activities")
router.register("social/participation", soc_api.EmployeeParticipationViewSet, "participation")

# Governance
router.register("governance/policies", gov_api.ESGPolicyViewSet, "policies")
router.register("governance/acknowledgements", gov_api.PolicyAcknowledgementViewSet, "acknowledgements")
router.register("governance/audits", gov_api.AuditViewSet, "audits")
router.register("governance/issues", gov_api.ComplianceIssueViewSet, "issues")

# Gamification
router.register("gamification/challenges", gam_api.ChallengeViewSet, "challenges")
router.register("gamification/challenge-participation", gam_api.ChallengeParticipationViewSet, "challenge-participation")
router.register("gamification/badges", gam_api.BadgeViewSet, "badges")
router.register("gamification/rewards", gam_api.RewardViewSet, "rewards")

# Notifications
router.register("notifications", notif_api.NotificationViewSet, "notifications")

api_urlpatterns = router.urls + [
    path("gamification/leaderboard/", LeaderboardView.as_view(), name="leaderboard"),
    path("gamification/my-profile/", MyProfileView.as_view(), name="my-profile"),
    path("reports/export/", ReportExportView.as_view(), name="report-export"),
]
