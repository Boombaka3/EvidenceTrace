# apps/evidence/models.py
from django.db import models


class AnalysisJob(models.Model):
    class Status(models.TextChoices):
        PENDING  = 'PENDING'
        RUNNING  = 'RUNNING'
        DONE     = 'DONE'
        FAILED   = 'FAILED'

    status        = models.CharField(max_length=20,
                                     choices=Status.choices,
                                     default=Status.PENDING)
    n_samples     = models.IntegerField(default=3)
    result_s3_key = models.CharField(max_length=500, blank=True)
    started_at    = models.DateTimeField(null=True, blank=True)
    finished_at   = models.DateTimeField(null=True, blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "evidence"

    def __str__(self):
        return f"AnalysisJob {self.id} [{self.status}]"


class Paper(models.Model):
    job             = models.ForeignKey(AnalysisJob,
                                        on_delete=models.CASCADE,
                                        related_name='papers')
    title           = models.CharField(max_length=500, blank=True)
    abstract        = models.TextField(blank=True)
    s3_key          = models.CharField(max_length=500)
    parsed_sections = models.JSONField(default=dict)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "evidence"

    def __str__(self):
        return f"Paper {self.id}: {self.title[:50]}"


class Claim(models.Model):
    class ClaimType(models.TextChoices):
        CAUSAL      = 'causal'
        COMPARATIVE = 'comparative'
        DESCRIPTIVE = 'descriptive'
        FACTUAL     = 'factual'

    paper           = models.ForeignKey(Paper,
                                        on_delete=models.CASCADE,
                                        related_name='claims')
    text            = models.TextField()
    claim_type      = models.CharField(max_length=20,
                                       choices=ClaimType.choices,
                                       default=ClaimType.FACTUAL)
    entities        = models.JSONField(default=list)
    section         = models.CharField(max_length=100, blank=True)
    source_sentence = models.TextField(blank=True)
    confidence      = models.FloatField(null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "evidence"

    def __str__(self):
        return f"Claim {self.id}: {self.text[:60]}"


class AnswerRecord(models.Model):
    class Answer(models.TextChoices):
        YES   = 'yes'
        NO    = 'no'
        MAYBE = 'maybe'

    paper           = models.ForeignKey(Paper,
                                        on_delete=models.CASCADE,
                                        related_name='answers')
    question        = models.TextField()
    answer          = models.CharField(max_length=10,
                                       choices=Answer.choices)
    gold_label      = models.CharField(max_length=10, blank=True)
    reasoning       = models.TextField(blank=True)
    source_sentence = models.TextField(blank=True)
    error_types     = models.JSONField(default=list,
                                       blank=True,
                                       help_text=(
                                           "EvidenceLens error taxonomy: "
                                           "overgeneralization, condition_dropping, "
                                           "false_certainty, missing_evidence, "
                                           "unsupported_claim, wrong_evidence, "
                                           "missing_limitation, "
                                           "contradiction_with_source, "
                                           "conflict_ignored, paper_section_misread"
                                       ))
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "evidence"

    def __str__(self):
        return f"AnswerRecord {self.id}: {self.answer} ({self.question[:40]})"


class RewardScore(models.Model):
    answer_record      = models.OneToOneField(AnswerRecord,
                                              on_delete=models.CASCADE,
                                              related_name='reward')
    consistency_score  = models.FloatField(null=True, blank=True)
    nli_score          = models.FloatField(null=True, blank=True)
    faithfulness_score = models.FloatField(null=True, blank=True)
    final_confidence   = models.FloatField(null=True, blank=True)
    n_samples          = models.IntegerField(default=1)
    created_at         = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "evidence"

    def __str__(self):
        conf = f"{self.final_confidence:.2f}" if self.final_confidence else "None"
        return f"RewardScore {self.id} confidence={conf}"


class AgentTrace(models.Model):
    class Role(models.TextChoices):
        THOUGHT     = 'thought'
        ACTION      = 'action'
        OBSERVATION = 'observation'
        ANSWER      = 'answer'
        ERROR       = 'error'

    class ToolName(models.TextChoices):
        RETRIEVE  = 'retrieve_answers'
        NLI       = 'nli_score'
        LLM       = 'llm_call'
        THRESHOLD = 'confidence_gate'
        NONE      = 'none'

    job           = models.ForeignKey(
                        'AnalysisJob',
                        on_delete=models.CASCADE,
                        related_name='traces'
                    )
    session_id    = models.CharField(max_length=64)
    iteration     = models.IntegerField(default=0)
    role          = models.CharField(max_length=20, choices=Role.choices)
    tool_name     = models.CharField(
                        max_length=30,
                        choices=ToolName.choices,
                        default=ToolName.NONE
                    )
    tool_input    = models.JSONField(default=dict)
    tool_output   = models.JSONField(default=dict)
    model_version = models.CharField(max_length=100, blank=True)
    latency_ms    = models.IntegerField(null=True)
    prompt_tokens = models.IntegerField(null=True)
    final_answer  = models.TextField(blank=True)
    confidence    = models.FloatField(null=True)
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "evidence"
        ordering = ['session_id', 'iteration']

    def __str__(self):
        return (
            f"AgentTrace job={self.job_id} session={self.session_id[:8]} "
            f"iter={self.iteration} role={self.role}"
        )
