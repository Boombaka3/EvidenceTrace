// frontend/src/pages/Suites.jsx
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { listSuites, createSuite } from '../api/client.js'

function emptyCriteria() {
  return { name: '', weight: '0.5' }
}

export default function Suites() {
  const [suites, setSuites] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showForm, setShowForm] = useState(false)

  // Form state
  const [formName, setFormName] = useState('')
  const [formVersion, setFormVersion] = useState('1')
  const [criteria, setCriteria] = useState([emptyCriteria()])
  const [formError, setFormError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const navigate = useNavigate()

  async function load() {
    setLoading(true)
    setError(null)
    try {
      setSuites(await listSuites())
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  function addCriterion() {
    setCriteria([...criteria, emptyCriteria()])
  }

  function updateCriterion(i, field, val) {
    const next = criteria.map((c, idx) => idx === i ? { ...c, [field]: val } : c)
    setCriteria(next)
  }

  function removeCriterion(i) {
    setCriteria(criteria.filter((_, idx) => idx !== i))
  }

  async function handleCreate(e) {
    e.preventDefault()
    setFormError(null)
    if (!formName.trim()) { setFormError('Suite name is required'); return }
    const rubric = {}
    for (const c of criteria) {
      if (c.name.trim()) rubric[c.name.trim()] = parseFloat(c.weight) || 0.5
    }
    setSubmitting(true)
    try {
      await createSuite({
        name: formName.trim(),
        version: parseInt(formVersion, 10) || 1,
        rubric,
      })
      setFormName('')
      setFormVersion('1')
      setCriteria([emptyCriteria()])
      setShowForm(false)
      await load()
    } catch (e) {
      setFormError(e.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold text-white">Suites</h1>
        <button
          onClick={() => { setShowForm(!showForm); setFormError(null) }}
          className="bg-indigo-500 hover:bg-indigo-600 text-white text-sm px-4 py-1.5 transition-colors"
        >
          {showForm ? 'Cancel' : '+ New Suite'}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleCreate} className="border border-slate-700 bg-slate-900 p-5 mb-6 space-y-4">
          <div className="text-sm font-medium text-slate-300 mb-2">New Suite</div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Suite name *</label>
              <input
                type="text"
                value={formName}
                onChange={e => setFormName(e.target.value)}
                className="w-full bg-slate-800 border border-slate-600 text-slate-200 text-sm px-3 py-1.5 focus:outline-none focus:border-indigo-500"
                placeholder="My eval suite"
              />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Version</label>
              <input
                type="number"
                min="1"
                value={formVersion}
                onChange={e => setFormVersion(e.target.value)}
                className="w-full bg-slate-800 border border-slate-600 text-slate-200 text-sm px-3 py-1.5 focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs text-slate-400">Rubric criteria</label>
              <button
                type="button"
                onClick={addCriterion}
                className="text-xs text-indigo-400 hover:text-indigo-300"
              >
                + Add criterion
              </button>
            </div>
            <div className="space-y-2">
              {criteria.map((c, i) => (
                <div key={i} className="flex gap-2 items-center">
                  <input
                    type="text"
                    value={c.name}
                    onChange={e => updateCriterion(i, 'name', e.target.value)}
                    placeholder="Criterion name"
                    className="flex-1 bg-slate-800 border border-slate-600 text-slate-200 text-sm px-3 py-1.5 focus:outline-none focus:border-indigo-500"
                  />
                  <input
                    type="number"
                    min="0"
                    max="1"
                    step="0.1"
                    value={c.weight}
                    onChange={e => updateCriterion(i, 'weight', e.target.value)}
                    className="w-20 bg-slate-800 border border-slate-600 text-slate-200 text-sm px-3 py-1.5 focus:outline-none focus:border-indigo-500"
                  />
                  {criteria.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeCriterion(i)}
                      className="text-slate-500 hover:text-red-400 text-sm px-1"
                    >
                      ×
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>

          {formError && <div className="text-red-400 text-sm">{formError}</div>}

          <div className="flex gap-3">
            <button
              type="submit"
              disabled={submitting}
              className="bg-indigo-500 hover:bg-indigo-600 disabled:opacity-50 text-white text-sm px-5 py-1.5 transition-colors"
            >
              {submitting ? 'Creating...' : 'Create'}
            </button>
            <button
              type="button"
              onClick={() => { setShowForm(false); setFormError(null) }}
              className="text-slate-400 hover:text-white text-sm px-4 py-1.5"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {loading && (
        <div className="flex items-center gap-2 text-slate-400 text-sm">
          <div className="w-4 h-4 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          Loading...
        </div>
      )}

      {error && (
        <div className="border border-red-700 bg-red-950 text-red-400 text-sm px-4 py-3">
          Error: {error}
        </div>
      )}

      {!loading && !error && suites.length === 0 && (
        <div className="text-slate-500 text-sm py-8 text-center border border-slate-700">
          No suites yet. Create one to get started.
        </div>
      )}

      {!loading && !error && suites.length > 0 && (
        <table className="w-full text-sm text-slate-200 border border-slate-700">
          <thead>
            <tr className="bg-slate-800 text-slate-400 text-xs uppercase">
              <th className="text-left px-3 py-2">Name</th>
              <th className="text-left px-3 py-2">Version</th>
              <th className="text-left px-3 py-2">Criteria</th>
              <th className="text-left px-3 py-2">Baseline</th>
              <th className="text-left px-3 py-2">Created</th>
              <th className="text-left px-3 py-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {suites.map(s => (
              <tr key={s.id} className="border-t border-slate-700 hover:bg-slate-800">
                <td className="px-3 py-2 font-medium text-white">{s.name}</td>
                <td className="px-3 py-2 font-mono text-xs">{s.version}</td>
                <td className="px-3 py-2 text-xs text-slate-400">
                  {s.rubric ? Object.keys(s.rubric).length : 0} criteria
                </td>
                <td className="px-3 py-2 text-xs font-mono text-slate-400">
                  {s.baseline_run_id ?? '--'}
                </td>
                <td className="px-3 py-2 text-xs text-slate-400">
                  {new Date(s.created_at).toLocaleDateString()}
                </td>
                <td className="px-3 py-2">
                  <button
                    onClick={() => navigate(`/suites/${s.id}`)}
                    className="text-indigo-400 hover:text-indigo-300 text-xs"
                  >
                    View Cases
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
