// frontend/src/pages/RunStatus.jsx
import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { getRun } from '../api/client.js'
import StatusBadge from '../components/StatusBadge.jsx'
import ProgressBar from '../components/ProgressBar.jsx'

const TERMINAL = ['DONE', 'FAILED']

const STATUS_MSG = {
  PENDING: 'Waiting for Celery worker to pick up the job...',
  DISPATCHED: (total) => `Dispatching ${total} model tasks...`,
  RUNNING: (progress, total) => `${progress} of ${total} model runs complete`,
  DONE: 'All runs complete. View results below.',
  FAILED: 'Run failed. Check Celery worker logs.',
}

function statusMessage(run) {
  if (!run) return ''
  const fn = STATUS_MSG[run.status]
  if (typeof fn === 'function') return fn(run.progress, run.total)
  return fn || run.status
}

function fmt(dt) {
  return dt ? new Date(dt).toLocaleString() : '--'
}

export default function RunStatus() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [run, setRun] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [polling, setPolling] = useState(false)
  const intervalRef = useRef(null)

  async function fetchRun() {
    try {
      const data = await getRun(id)
      setRun(data)
      if (TERMINAL.includes(data.status)) {
        clearInterval(intervalRef.current)
        setPolling(false)
      }
      return data
    } catch (e) {
      setError(e.message)
      clearInterval(intervalRef.current)
      setPolling(false)
    }
  }

  useEffect(() => {
    async function init() {
      setLoading(true)
      const data = await fetchRun()
      setLoading(false)
      if (data && !TERMINAL.includes(data.status)) {
        setPolling(true)
        intervalRef.current = setInterval(fetchRun, 3000)
      }
    }
    init()
    return () => clearInterval(intervalRef.current)
  }, [id])

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

  if (!run) return null

  return (
    <div className="max-w-2xl space-y-6">
      <div className="flex items-center gap-3">
        <h1 className="text-xl font-semibold text-white">Run #{run.id}</h1>
        <StatusBadge status={run.status} large />
        {polling && (
          <span className="w-2 h-2 rounded-full bg-indigo-400 animate-pulse inline-block" title="Polling..." />
        )}
      </div>

      <div className="border border-slate-700 bg-slate-900 p-5 space-y-4">
        <ProgressBar current={run.progress} total={run.total} />

        <p className="text-sm text-slate-300">{statusMessage(run)}</p>

        <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-xs">
          <div>
            <span className="text-slate-500">Suite ID</span>
            <span className="ml-2 font-mono text-slate-300">{run.suite_id}</span>
          </div>
          <div>
            <span className="text-slate-500">Score mode</span>
            <span className="ml-2 font-mono text-slate-300">{run.score_mode}</span>
          </div>
          <div>
            <span className="text-slate-500">Started</span>
            <span className="ml-2 text-slate-300">{fmt(run.started_at)}</span>
          </div>
          <div>
            <span className="text-slate-500">Finished</span>
            <span className="ml-2 text-slate-300">{fmt(run.finished_at)}</span>
          </div>
        </div>
      </div>

      {run.status === 'DONE' && (
        <button
          onClick={() => navigate(`/runs/${id}/results`)}
          className="bg-green-600 hover:bg-green-700 text-white text-sm px-5 py-2 transition-colors"
        >
          View Results →
        </button>
      )}

      {run.status === 'FAILED' && (
        <Link
          to="/suites"
          className="inline-block text-slate-400 hover:text-white text-sm"
        >
          ← Back to Suites
        </Link>
      )}
    </div>
  )
}
