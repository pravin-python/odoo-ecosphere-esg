from django.urls import path

from . import views

app_name = "core_v1"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
]
