# apps/evidence/admin.py
from django.contrib import admin

from .models import AgentTrace, AnalysisJob, AnswerRecord, Claim, Paper, RewardScore


@admin.register(AnalysisJob)
class AnalysisJobAdmin(admin.ModelAdmin):
    list_display = ['id', 'status', 'n_samples', 'created_at']
    list_filter  = ['status']


@admin.register(Paper)
class PaperAdmin(admin.ModelAdmin):
    list_display  = ['id', 'title', 'job', 'created_at']
    search_fields = ['title']


@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    list_display = ['id', 'claim_type', 'section', 'confidence', 'paper']
    list_filter  = ['claim_type', 'section']


@admin.register(AnswerRecord)
class AnswerRecordAdmin(admin.ModelAdmin):
    list_display = ['id', 'answer', 'question_preview', 'paper']
    list_filter  = ['answer']

    def question_preview(self, obj):
        return obj.question[:60]
    question_preview.short_description = 'Question'


@admin.register(RewardScore)
class RewardScoreAdmin(admin.ModelAdmin):
    list_display = ['id', 'consistency_score', 'final_confidence', 'n_samples']


@admin.register(AgentTrace)
class AgentTraceAdmin(admin.ModelAdmin):
    list_display  = ['id', 'job', 'session_id_short', 'iteration', 'role', 'tool_name', 'latency_ms', 'created_at']
    list_filter   = ['role', 'tool_name']
    search_fields = ['session_id', 'job__id']

    def session_id_short(self, obj):
        return obj.session_id[:8]
    session_id_short.short_description = 'Session'
