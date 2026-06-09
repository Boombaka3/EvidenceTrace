// frontend/src/api/client.js
const API_BASE = import.meta.env.VITE_API_BASE || '/api'
const API_KEY = import.meta.env.VITE_API_KEY || ''

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': API_KEY,
      ...options.headers,
    },
  })
  if (!res.ok) {
    let msg = `HTTP ${res.status}`
    try {
      const body = await res.json()
      msg = body.detail || body.message || JSON.stringify(body)
    } catch (_) {}
    throw new Error(msg)
  }
  if (res.status === 204) return null
  return res.json()
}

// Suites
export async function listSuites() {
  return request('/evals/suites/')
}

export async function createSuite(data) {
  return request('/evals/suites/', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function getSuite(id) {
  return request(`/evals/suites/${id}/`)
}

export async function patchSuite(id, data) {
  return request(`/evals/suites/${id}/`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}

// Cases
export async function listCases(suiteId) {
  return request(`/evals/suites/${suiteId}/cases/`)
}

export async function createCase(suiteId, data) {
  return request(`/evals/suites/${suiteId}/cases/`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function deleteCase(caseId) {
  return request(`/evals/cases/${caseId}/`, { method: 'DELETE' })
}

// Runs
export async function createRun(data) {
  return request('/evals/runs/', {
    method: 'POST',
    body: JSON.stringify({
      suite_id: data.suite_id,
      model_ids: data.model_ids,
      score_mode: data.score_mode,
      baseline_run_id: data.baseline_run_id || null,
    }),
  })
}

export async function getRun(runId) {
  return request(`/evals/runs/${runId}/`)
}

export async function getRunResults(runId) {
  return request(`/evals/runs/${runId}/results/`)
}

export async function getRegression(runId) {
  return request(`/evals/runs/${runId}/regression/`)
}

export async function pinBaseline(runId) {
  return request(`/evals/runs/${runId}/pin-baseline/`, { method: 'POST' })
}

// Models
export async function listModels() {
  return request('/evals/models/')
}
