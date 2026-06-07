# apps/evals/admin.py
from django.contrib import admin

from .models import EvalRun, EvalSuite, ModelRun, PromptCase, ScoreResult


@admin.register(EvalSuite)
class EvalSuiteAdmin(admin.ModelAdmin):
    list_display = ["name", "version", "created_at"]
    search_fields = ["name"]


@admin.register(PromptCase)
class PromptCaseAdmin(admin.ModelAdmin):
    list_display = ["name", "suite", "created_at"]
    list_filter = ["suite"]
    search_fields = ["name"]


@admin.register(EvalRun)
class EvalRunAdmin(admin.ModelAdmin):
    list_display = ["id", "suite", "status", "score_mode", "started_at", "finished_at"]
    list_filter = ["status", "score_mode"]
    readonly_fields = ["started_at", "finished_at", "result_s3_key"]


@admin.register(ModelRun)
class ModelRunAdmin(admin.ModelAdmin):
    list_display = ["id", "eval_run", "model_id", "status", "latency_ms", "created_at"]
    list_filter = ["status", "model_id"]
    readonly_fields = ["raw_output", "s3_key", "error_message"]


@admin.register(ScoreResult)
class ScoreResultAdmin(admin.ModelAdmin):
    list_display = ["id", "model_run", "overall", "passed", "regression_delta", "created_at"]
    list_filter = ["passed"]
    readonly_fields = ["scores", "judge_reasoning"]
