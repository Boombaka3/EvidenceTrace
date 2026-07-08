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
    question: 'Does the evidence support that glutamate mediates energy balance?',
    answer: 'yes',
    reasoning: 'The abstract states glutamatergic neurotransmission from PVH Sim1 neurons is required for MC4R-mediated control of energy balance.',
    source_sentence: 'Glutamatergic neurotransmission from PVH Sim1 neurons is required for MC4R-mediated control of energy balance.',
    final_confidence: 0.97,
    consistency_score: 1.0,
    faithfulness_score: 1.0,
    paper_id: 1,
    paper_title: 'Glutamate mediates MC4R function in body weight regulation',
    error_types: [],
  },
  {
    id: 2,
    question: 'Does the evidence support that HPV co-testing detects more CIN2+ lesions?',
    answer: 'yes',
    reasoning: 'HPV co-testing identified significantly more CIN2+ lesions at baseline.',
    source_sentence: 'HPV co-testing identified significantly more CIN2+ lesions at baseline compared to cytology alone.',
    final_confidence: 0.98,
    consistency_score: 1.0,
    faithfulness_score: 0.94,
    paper_id: 3,
    paper_title: 'HPV and Pap co-testing in cervical cancer screening',
    error_types: [],
  },
  {
    id: 3,
    question: 'Does the evidence support that IFN-gamma receptor deficiency worsens myocarditis?',
    answer: 'yes',
    reasoning: 'Mice lacking the IFN-gamma receptor develop severe and persistent EAM.',
    source_sentence: 'Mice lacking the IFN-gamma receptor develop severe and persistent experimental autoimmune myocarditis.',
    final_confidence: 0.98,
    consistency_score: 1.0,
    faithfulness_score: 0.93,
    paper_id: 5,
    paper_title: 'IFN-gamma receptor deficiency causes severe myocarditis',
    error_types: [],
  },
]

export const MOCK_MODELS = [
  'llama-3.3-70b-instruct',
  'medgemma-27b-it',
  'mistral-small-3.1',
  'gpt-oss-120b',
  'gemma-3-27b-it',
]
