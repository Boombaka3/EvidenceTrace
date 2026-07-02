const BASE = import.meta.env.VITE_API_BASE || '/api'

function getApiKey() {
  return sessionStorage.getItem('et_api_key') ||
         import.meta.env.VITE_API_KEY ||
         ''
}

function getHeaders(requiresAuth = false) {
  const h = { 'Content-Type': 'application/json' }
  const apiKey = getApiKey()
  if (requiresAuth && apiKey) h['X-API-Key'] = apiKey
  return h
}

async function request(method, path, body, requiresAuth = false) {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: getHeaders(requiresAuth),
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`${res.status}: ${text}`)
  }
  if (res.status === 204) return null
  return res.json()
}

export const listJobs = () => request('GET', '/evidence/jobs/')
export const getJob = (id) => request('GET', `/evidence/jobs/${id}/`)
export const listPapers = (id) => request('GET', `/evidence/jobs/${id}/papers/`)
export const listClaims = (id) => request('GET', `/evidence/jobs/${id}/claims/`)
export const getReport = (id) => request('GET', `/evidence/jobs/${id}/report/`)
export const getHealth = () => request('GET', '/health/')

export const createJob = (data) => request('POST', '/evidence/jobs/', data, true)
export const dispatchJob = (id) => request('POST', `/evidence/jobs/${id}/dispatch/`, {}, true)
export const dispatchJobSync = (id) => request('POST', `/evidence/jobs/${id}/dispatch-sync/`, {}, true)

export async function uploadPaper(jobId, file, title = '') {
  const form = new FormData()
  form.append('pdf_file', file)
  if (title) form.append('title', title)

  const headers = {}
  const apiKey = getApiKey()
  if (apiKey) headers['X-API-Key'] = apiKey

  const res = await fetch(`${BASE}/evidence/jobs/${jobId}/papers/`, {
    method: 'POST',
    headers,
    body: form,
  })
  if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`)
  return res.json()
}

export const listAnswers = (id) => request('GET', `/evidence/jobs/${id}/answers/`)
export const chatWithJob = (id, question) => request('POST', `/evidence/jobs/${id}/chat/`, { question })

export async function deletePaper(paperId) {
  const headers = {}
  const apiKey = getApiKey()
  if (apiKey) headers['X-API-Key'] = apiKey

  const res = await fetch(`${BASE}/evidence/papers/${paperId}/`, {
    method: 'DELETE',
    headers,
  })
  if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`)
  return true
}
