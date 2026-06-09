# llm_eval_harness/config/urls.py
from django.contrib import admin
from django.urls import path, re_path
from django.views.generic import TemplateView
from ninja import NinjaAPI, Router

from apps.evals.router import router as evals_router

api = NinjaAPI(title="LLM Eval Harness", version="1.0.0", docs_url="/docs")

# ── Health check ──────────────────────────────────────────────────────────────
health_router = Router(tags=["health"])


@health_router.get("/health/")
def health(request):
    return {"status": "ok"}


api.add_router("", health_router)
api.add_router("/evals", evals_router)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
    re_path(
        r"^(?!api/).*$",
        TemplateView.as_view(template_name="index.html"),
        name="frontend",
    ),
]
