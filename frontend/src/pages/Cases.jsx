// frontend/src/pages/Cases.jsx
import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { getSuite, listCases, createCase, deleteCase } from '../api/client.js'

function trunc(str, n) {
  if (!str) return '--'
  return str.length > n ? str.slice(0, n) + '…' : str
}

export default function Cases() {
  const { id } = useParams()
  const navigate = useNavigate()

  const [suite, setSuite] = useState(null)
  const [cases, setCases] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showForm, setShowForm] = useState(false)

  const [formName, setFormName] = useState('')
  const [formSystem, setFormSystem] = useState('')
  const [formUser, setFormUser] = useState('')
  const [formExpected, setFormExpected] = useState('')
  const [formError, setFormError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const [s, c] = await Promise.all([getSuite(id), listCases(id)])
      setSuite(s)
      setCases(c)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [id])

  async function handleDelete(caseId) {
    if (!window.confirm('Delete this case?')) return
    try {
      await deleteCase(caseId)
      await load()
    } catch (e) {
      alert('Delete failed: ' + e.message)
    }
  }

  async function handleAdd(e) {
    e.preventDefault()
    setFormError(null)
    if (!formName.trim()) { setFormError('Name is required'); return }
    if (!formUser.trim()) { setFormError('User prompt is required'); return }
    setSubmitting(true)
    try {
      await createCase(id, {
        name: formName.trim(),
        system_prompt: formSystem.trim(),
        user_prompt: formUser.trim(),
        expected_output: formExpected.trim() || null,
        tags: [],
      })
      setFormName(''); setFormSystem(''); setFormUser(''); setFormExpected('')
      setShowForm(false)
      await load()
    } catch (e) {
      setFormError(e.message)
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
    <div>
      <div className="mb-5">
        <Link to="/suites" className="text-slate-400 hover:text-white text-sm">
          ← Back to Suites
        </Link>
        <div className="mt-3 flex items-baseline gap-3">
          <h1 className="text-xl font-semibold text-white">{suite?.name}</h1>
          <span className="text-slate-400 text-sm">Cases</span>
        </div>
      </div>

      <div className="flex items-center justify-between mb-4">
        <span className="text-sm text-slate-400">{cases.length} case{cases.length !== 1 ? 's' : ''}</span>
        <button
          onClick={() => { setShowForm(!showForm); setFormError(null) }}
          className="bg-indigo-500 hover:bg-indigo-600 text-white text-sm px-4 py-1.5 transition-colors"
        >
          {showForm ? 'Cancel' : '+ Add Case'}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleAdd} className="border border-slate-700 bg-slate-900 p-5 mb-6 space-y-4">
          <div className="text-sm font-medium text-slate-300">Add Case</div>

          <div>
            <label className="block text-xs text-slate-400 mb-1">Case name *</label>
            <input
              type="text"
              value={formName}
              onChange={e => setFormName(e.target.value)}
              className="w-full bg-slate-800 border border-slate-600 text-slate-200 text-sm px-3 py-1.5 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div>
            <label className="block text-xs text-slate-400 mb-1">System prompt</label>
            <textarea
              rows={3}
              value={formSystem}
              onChange={e => setFormSystem(e.target.value)}
              className="w-full bg-slate-800 border border-slate-600 text-slate-200 text-sm px-3 py-1.5 focus:outline-none focus:border-indigo-500 resize-y font-mono"
            />
          </div>

          <div>
            <label className="block text-xs text-slate-400 mb-1">User prompt *</label>
            <textarea
              rows={3}
              value={formUser}
              onChange={e => setFormUser(e.target.value)}
              className="w-full bg-slate-800 border border-slate-600 text-slate-200 text-sm px-3 py-1.5 focus:outline-none focus:border-indigo-500 resize-y font-mono"
            />
          </div>

          <div>
            <label className="block text-xs text-slate-400 mb-1">Expected output</label>
            <textarea
              rows={2}
              value={formExpected}
              onChange={e => setFormExpected(e.target.value)}
              placeholder="Leave blank for LLM judge scoring"
              className="w-full bg-slate-800 border border-slate-600 text-slate-200 text-sm px-3 py-1.5 focus:outline-none focus:border-indigo-500 resize-y font-mono placeholder-slate-600"
            />
          </div>

          {formError && <div className="text-red-400 text-sm">{formError}</div>}

          <div className="flex gap-3">
            <button
              type="submit"
              disabled={submitting}
              className="bg-indigo-500 hover:bg-indigo-600 disabled:opacity-50 text-white text-sm px-5 py-1.5"
            >
              {submitting ? 'Adding...' : 'Add Case'}
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

      {cases.length === 0 ? (
        <div className="text-slate-500 text-sm py-8 text-center border border-slate-700">
          No cases yet. Add one to run evaluations.
        </div>
      ) : (
        <table className="w-full text-sm text-slate-200 border border-slate-700">
          <thead>
            <tr className="bg-slate-800 text-slate-400 text-xs uppercase">
              <th className="text-left px-3 py-2">Name</th>
              <th className="text-left px-3 py-2">System Prompt</th>
              <th className="text-left px-3 py-2">User Prompt</th>
              <th className="text-left px-3 py-2">Expected Output</th>
              <th className="text-left px-3 py-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {cases.map(c => (
              <tr key={c.id} className="border-t border-slate-700 hover:bg-slate-800">
                <td className="px-3 py-2 font-medium text-white">{c.name}</td>
                <td className="px-3 py-2 text-slate-400 font-mono text-xs">{trunc(c.system_prompt, 60)}</td>
                <td className="px-3 py-2 text-slate-300 font-mono text-xs">{trunc(c.user_prompt, 60)}</td>
                <td className="px-3 py-2 text-slate-400 font-mono text-xs">{trunc(c.expected_output, 40)}</td>
                <td className="px-3 py-2">
                  <button
                    onClick={() => handleDelete(c.id)}
                    className="text-red-400 hover:text-red-300 text-xs"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <div className="mt-8 pt-6 border-t border-slate-700">
        <button
          onClick={() => navigate(`/runs/new?suite_id=${id}`)}
          className="bg-green-600 hover:bg-green-700 text-white text-sm px-5 py-2 transition-colors"
        >
          Run this suite →
        </button>
      </div>
    </div>
  )
}
