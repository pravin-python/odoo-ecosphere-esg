from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from apps.environmental.v1.dashboard_api import DashboardSummaryView

from .api import api_urlpatterns

# Versioned API surface. Each app owns its own v1 api module.
api_v1_patterns = [
    path("", include("apps.accounts.v1.urls")),
    path("dashboard/summary/", DashboardSummaryView.as_view(), name="dashboard-summary"),
    *api_urlpatterns,
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include((api_v1_patterns, "api-v1"))),
    path("", include("apps.core.v1.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
