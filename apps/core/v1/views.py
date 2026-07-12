from django.views.generic import TemplateView


class HomeView(TemplateView):
    """Splash page that JS-redirects to /dashboard/ or /login/ based on auth."""

    template_name = "core/v1/index.html"


class LoginPageView(TemplateView):
    template_name = "accounts/v1/login.html"


class RegisterPageView(TemplateView):
    template_name = "accounts/v1/register.html"


class DashboardPageView(TemplateView):
    template_name = "accounts/v1/dashboard.html"
