export const MOCK_JOBS = [
  {
    id: 1,
    status: 'DONE',
    n_samples: 3,
    paper_count: 3,
    claim_count: 12,
    answer_count: 8,
    started_at: '2026-06-13T10:00:00Z',
    finished_at: '2026-06-13T10:02:30Z',
    created_at: '2026-06-13T09:59:00Z',
  },
  {
    id: 2,
    status: 'RUNNING',
    n_samples: 1,
    paper_count: 2,
    claim_count: 5,
    answer_count: 0,
    started_at: '2026-06-13T14:00:00Z',
    finished_at: null,
    created_at: '2026-06-13T13:59:00Z',
  },
]

export const MOCK_PAPERS = [
  { id: 1, job_id: 1, title: 'Drug X efficacy in mouse tumor models', claim_count: 6, created_at: '2026-06-13T10:01:00Z' },
  { id: 2, job_id: 1, title: 'Drug X Phase 2 clinical trial results', claim_count: 6, created_at: '2026-06-13T10:01:30Z' },
  { id: 3, job_id: 1, title: 'Drug X mechanism of action study', claim_count: 0, created_at: '2026-06-13T10:02:00Z' },
]

export const MOCK_ANSWERS = [
  {
    id: 1,
    question: 'Does Drug X improve progression-free survival?',
    answer: 'yes',
    reasoning: 'The trial abstract reports improved progression-free survival versus control.',
    source_sentence: 'Patients receiving Drug X had significantly longer progression-free survival than placebo.',
    final_confidence: 0.92,
    paper_title: 'Drug X Phase 2 clinical trial results',
    error_types: [],
    created_at: '2026-06-13T10:02:00Z',
  },
  {
    id: 2,
    question: 'Was toxicity reduced in the treatment arm?',
    answer: 'maybe',
    reasoning: 'The paper mentions manageable safety findings but does not directly compare lower toxicity.',
    source_sentence: 'Adverse events were consistent with prior studies and manageable with dose adjustments.',
    final_confidence: 0.58,
    paper_title: 'Drug X efficacy in mouse tumor models',
    error_types: ['low_confidence'],
    created_at: '2026-06-13T10:02:05Z',
  },
  {
    id: 3,
    question: 'Did the study evaluate immune infiltration?',
    answer: 'no',
    reasoning: 'The abstract focuses on tumor response and signaling pathways, not immune infiltration.',
    source_sentence: 'Tumor growth inhibition correlated with downstream MAPK suppression in treated mice.',
    final_confidence: 0.88,
    paper_title: 'Drug X mechanism of action study',
    error_types: [],
    created_at: '2026-06-13T10:02:10Z',
  },
]

export const MOCK_MODELS = [
  'llama-3.3-70b-instruct',
  'medgemma-27b-it',
  'mistral-small-3.1',
  'gpt-oss-120b',
  'gemma-3-27b-it',
]
