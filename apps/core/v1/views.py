from django.views.generic import TemplateView


class HomeView(TemplateView):
    template_name = "core/v1/index.html"
