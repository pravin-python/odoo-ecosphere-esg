from django.views.generic import TemplateView

# Per-module accent classes (literal strings so Tailwind's CDN picks them up).
MODULE_CONFIG = {
    "environmental": {"module_title": "Environmental", "accent_text": "text-emerald-400",
                      "accent_btn": "bg-emerald-600 hover:bg-emerald-700"},
    "social": {"module_title": "Social", "accent_text": "text-sky-400",
               "accent_btn": "bg-sky-600 hover:bg-sky-700"},
    "governance": {"module_title": "Governance", "accent_text": "text-violet-400",
                   "accent_btn": "bg-violet-600 hover:bg-violet-700"},
    "gamification": {"module_title": "Gamification", "accent_text": "text-amber-400",
                     "accent_btn": "bg-amber-600 hover:bg-amber-700"},
    "reports": {"module_title": "Reports", "accent_text": "text-slate-200",
                "accent_btn": "bg-slate-700 hover:bg-slate-600"},
    "settings": {"module_title": "Settings", "accent_text": "text-slate-200",
                 "accent_btn": "bg-slate-700 hover:bg-slate-600"},
}


class HomeView(TemplateView):
    """Splash page that JS-redirects to /dashboard/ or /login/ based on auth."""

    template_name = "core/v1/index.html"


class LoginPageView(TemplateView):
    template_name = "accounts/v1/login.html"


class RegisterPageView(TemplateView):
    template_name = "accounts/v1/register.html"


class DashboardPageView(TemplateView):
    template_name = "dashboard/v1/index.html"


class ModulePageView(TemplateView):
    """Shared module screen: tab bar + actions + data area, per the mockup."""

    template_name = "modules/v1/module.html"
    page = None

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["module_page"] = self.page
        ctx.update(MODULE_CONFIG.get(self.page, {}))
        return ctx
