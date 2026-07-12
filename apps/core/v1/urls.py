from django.urls import path

from . import views

app_name = "core_v1"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("login/", views.LoginPageView.as_view(), name="login"),
    path("register/", views.RegisterPageView.as_view(), name="register"),
    path("dashboard/", views.DashboardPageView.as_view(), name="dashboard"),

    # Module screens (one shared template; sub-tabs via ?tab=).
    path("environmental/", views.ModulePageView.as_view(page="environmental"), name="environmental"),
    path("social/", views.ModulePageView.as_view(page="social"), name="social"),
    path("governance/", views.ModulePageView.as_view(page="governance"), name="governance"),
    path("gamification/", views.ModulePageView.as_view(page="gamification"), name="gamification"),
    path("reports/", views.ModulePageView.as_view(page="reports"), name="reports"),
    path("settings/", views.ModulePageView.as_view(page="settings"), name="settings"),
]
