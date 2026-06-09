// frontend/src/pages/NewRun.jsx
import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { listSuites, listModels, createRun } from '../api/client.js'

const SCORE_MODES = [
  { value: 'exact_match', label: 'Exact Match -- compare to expected output' },
  { value: 'rubric', label: 'Rubric -- score against suite criteria' },
  { value: 'llm_judge', label: 'LLM Judge -- Claude evaluates quality' },
  { value: 'regression', label: 'Regression -- compare against baseline run' },
]

export default function NewRun() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const preselectedSuiteId = searchParams.get('suite_id')

  const [suites, setSuites] = useState([])
  const [models, setModels] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const [suiteId, setSuiteId] = useState(preselectedSuiteId || '')
  const [selectedModels, setSelectedModels] = useState([])
  const [scoreMode, setScoreMode] = useState('exact_match')
  const [baselineRunId, setBaselineRunId] = useState('')
  const [submitError, setSubmitError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    async function load() {
      try {
        const [s, m] = await Promise.all([listSuites(), listModels()])
        setSuites(s)
        setModels(m)
        if (preselectedSuiteId && !suiteId) setSuiteId(preselectedSuiteId)
      } catch (e) {
        setError(e.message)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  function toggleModel(model) {
    setSelectedModels(prev =>
      prev.includes(model) ? prev.filter(m => m !== model) : [...prev, model]
    )
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setSubmitError(null)
    if (!suiteId) { setSubmitError('Select a suite'); return }
    if (selectedModels.length === 0) { setSubmitError('Select at least one model'); return }
    setSubmitting(true)
    try {
      const run = await createRun({
        suite_id: parseInt(suiteId, 10),
        model_ids: selectedModels,
        score_mode: scoreMode,
        baseline_run_id: scoreMode === 'regression' && baselineRunId
          ? parseInt(baselineRunId, 10)
          : null,
      })
      navigate(`/runs/${run.id}`)
    } catch (e) {
      setSubmitError(e.message)
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-slate-400 text-sm">
        <div className="w-4 h-4 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
        Loading...
      </div>
    )
  }

  if (error) {
    return (
      <div className="border border-red-700 bg-red-950 text-red-400 text-sm px-4 py-3">
        Error: {error}
      </div>
    )
  }

  return (
    <div className="max-w-2xl">
      <h1 className="text-xl font-semibold text-white mb-6">New Run</h1>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Suite */}
        <div>
          <label className="block text-xs text-slate-400 mb-1.5 uppercase tracking-wide">Suite</label>
          <select
            value={suiteId}
            onChange={e => setSuiteId(e.target.value)}
            className="w-full bg-slate-800 border border-slate-600 text-slate-200 text-sm px-3 py-2 focus:outline-none focus:border-indigo-500"
          >
            <option value="">-- Select a suite --</option>
            {suites.map(s => (
              <option key={s.id} value={s.id}>{s.name} (v{s.version})</option>
            ))}
          </select>
        </div>

        {/* Models */}
        <div>
          <label className="block text-xs text-slate-400 mb-1.5 uppercase tracking-wide">
            Models <span className="text-slate-600 normal-case">(select one or more)</span>
          </label>
          <div className="border border-slate-700 divide-y divide-slate-700 max-h-64 overflow-y-auto">
            {models.map(m => (
              <label
                key={m}
                className="flex items-center gap-3 px-3 py-2 hover:bg-slate-800 cursor-pointer"
              >
                <input
                  type="checkbox"
                  checked={selectedModels.includes(m)}
                  onChange={() => toggleModel(m)}
                  className="accent-indigo-500"
                />
                <span className="font-mono text-sm text-slate-200">{m}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Score mode */}
        <div>
          <label className="block text-xs text-slate-400 mb-1.5 uppercase tracking-wide">Score Mode</label>
          <div className="space-y-2">
            {SCORE_MODES.map(({ value, label }) => (
              <label key={value} className="flex items-start gap-3 cursor-pointer">
                <input
                  type="radio"
                  name="scoreMode"
                  value={value}
                  checked={scoreMode === value}
                  onChange={() => setScoreMode(value)}
                  className="mt-0.5 accent-indigo-500"
                />
                <span className="text-sm text-slate-300">{label}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Baseline run ID (regression only) */}
        {scoreMode === 'regression' && (
          <div>
            <label className="block text-xs text-slate-400 mb-1.5 uppercase tracking-wide">
              Baseline Run ID
            </label>
            <input
              type="text"
              value={baselineRunId}
              onChange={e => setBaselineRunId(e.target.value)}
              placeholder="Enter baseline EvalRun ID"
              className="w-full bg-slate-800 border border-slate-600 text-slate-200 text-sm px-3 py-2 focus:outline-none focus:border-indigo-500 font-mono"
            />
          </div>
        )}

        {submitError && (
          <div className="border border-red-700 bg-red-950 text-red-400 text-sm px-4 py-3">
            {submitError}
          </div>
        )}

        <button
          type="submit"
          disabled={submitting}
          className="w-full bg-indigo-500 hover:bg-indigo-600 disabled:opacity-50 text-white text-sm py-2.5 font-medium transition-colors"
        >
          {submitting ? 'Dispatching...' : 'Dispatch Run'}
        </button>
      </form>
    </div>
  )
}
