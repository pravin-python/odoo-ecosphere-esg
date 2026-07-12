from django.urls import path

from . import views

app_name = "core_v1"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("login/", views.LoginPageView.as_view(), name="login"),
    path("register/", views.RegisterPageView.as_view(), name="register"),
    path("dashboard/", views.DashboardPageView.as_view(), name="dashboard"),
]
