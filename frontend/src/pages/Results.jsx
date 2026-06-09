// frontend/src/pages/Results.jsx
import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getRun, getRunResults, getRegression } from '../api/client.js'
import ScoreBar from '../components/ScoreBar.jsx'
import ModelCompare from '../components/ModelCompare.jsx'

function trunc(str, n) {
  if (!str) return '--'
  return str.length > n ? str.slice(0, n) + '…' : str
}

function StatBox({ label, value }) {
  return (
    <div className="border border-slate-700 bg-slate-800 px-4 py-3">
      <div className="text-2xl font-bold text-white font-mono">{value}</div>
      <div className="text-xs text-slate-400 mt-1">{label}</div>
    </div>
  )
}

function RegressionRow({ item }) {
  const delta = item.delta
  const abs = delta != null ? Math.abs(delta) : null
  const status = delta == null ? '--' : abs <= 0.05 ? 'Unchanged' : delta > 0 ? 'Improved' : 'Regressed'
  const statusColor = status === 'Improved' ? 'text-green-400' : status === 'Regressed' ? 'text-red-400' : 'text-slate-400'

  return (
    <tr className="border-t border-slate-700 hover:bg-slate-800">
      <td className="px-3 py-2 font-mono text-xs text-slate-300">{item.prompt_case_id}</td>
      <td className="px-3 py-2 font-mono text-xs text-slate-300">{item.model_id}</td>
      <td className="px-3 py-2 font-mono text-xs text-slate-400">--</td>
      <td className="px-3 py-2">
        {item.passed !== null ? (item.passed ?
          <span className="text-green-400">✓</span> :
          <span className="text-red-400">✗</span>
        ) : '--'}
      </td>
      <td className="px-3 py-2 font-mono text-xs">
        {delta == null ? '--' : delta > 0 ?
          <span className="text-green-400">+{delta.toFixed(3)}</span> :
          <span className="text-red-400">{delta.toFixed(3)}</span>
        }
      </td>
      <td className={`px-3 py-2 text-xs font-medium ${statusColor}`}>{status}</td>
    </tr>
  )
}

export default function Results() {
  const { id } = useParams()
  const [run, setRun] = useState(null)
  const [results, setResults] = useState([])
  const [regression, setRegression] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [expanded, setExpanded] = useState({})

  useEffect(() => {
    async function load() {
      try {
        const [r, res] = await Promise.all([getRun(id), getRunResults(id)])
        setRun(r)
        setResults(res)
        if (r.baseline_run_id) {
          try {
            setRegression(await getRegression(id))
          } catch (_) {}
        }
      } catch (e) {
        setError(e.message)
      } finally {
        setLoading(false)
      }
    }
    load()
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

  const passed = results.filter(r => r.passed === true).length
  const passRate = results.length > 0 ? Math.round((passed / results.length) * 100) + '%' : '--'
  const overallValues = results.map(r => r.overall).filter(v => v != null)
  const avgOverall = overallValues.length > 0
    ? (overallValues.reduce((a, b) => a + b, 0) / overallValues.length).toFixed(2)
    : '--'
  const modelSet = [...new Set(results.map(r => r.model_run_id))]

  // Group results by case
  const byCaseId = {}
  for (const r of results) {
    const key = r.model_run_id
    if (!byCaseId[key]) byCaseId[key] = []
    byCaseId[key].push(r)
  }

  return (
    <div className="space-y-8">
      <div>
        <Link to={`/runs/${id}`} className="text-slate-400 hover:text-white text-sm">
          ← Back to Run Status
        </Link>
        <h1 className="text-xl font-semibold text-white mt-3">Results -- Run #{id}</h1>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-4 gap-3">
        <StatBox label="Total results" value={results.length} />
        <StatBox label="Models tested" value={run?.model_ids?.length ?? '--'} />
        <StatBox label="Avg score" value={avgOverall} />
        <StatBox label="Pass rate" value={passRate} />
      </div>

      {/* Model comparison */}
      {results.length > 0 && (
        <div>
          <h2 className="text-sm font-medium text-slate-300 mb-3 uppercase tracking-wide">Model Comparison</h2>
          <ModelCompare results={results} />
        </div>
      )}

      {/* Full results table */}
      <div>
        <h2 className="text-sm font-medium text-slate-300 mb-3 uppercase tracking-wide">All Results</h2>
        <table className="w-full text-sm text-slate-200 border border-slate-700">
          <thead>
            <tr className="bg-slate-800 text-slate-400 text-xs uppercase">
              <th className="text-left px-3 py-2">ID</th>
              <th className="text-left px-3 py-2">Model</th>
              <th className="text-left px-3 py-2">Score</th>
              <th className="text-left px-3 py-2">Passed</th>
              <th className="text-left px-3 py-2">Latency</th>
            </tr>
          </thead>
          <tbody>
            {results.map(r => (
              <tr key={r.id} className="border-t border-slate-700 hover:bg-slate-800">
                <td className="px-3 py-2 font-mono text-xs text-slate-400">{r.id}</td>
                <td className="px-3 py-2 font-mono text-xs">{r.model_id || r.model_run_id}</td>
                <td className="px-3 py-2">
                  <ScoreBar value={r.overall} width="100px" />
                </td>
                <td className="px-3 py-2">
                  {r.passed === null || r.passed === undefined ? '--' : r.passed ?
                    <span className="text-green-400">✓</span> :
                    <span className="text-red-400">✗</span>
                  }
                </td>
                <td className="px-3 py-2 font-mono text-xs text-slate-400">
                  {r.latency_ms != null ? `${r.latency_ms}ms` : '--'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Regression report */}
      {regression && (
        <div>
          <h2 className="text-sm font-medium text-slate-300 mb-3 uppercase tracking-wide">
            Regression Report
            <span className="ml-2 text-slate-500 normal-case text-xs font-normal">
              vs baseline run #{regression.baseline_run_id}
            </span>
          </h2>
          <table className="w-full text-sm text-slate-200 border border-slate-700">
            <thead>
              <tr className="bg-slate-800 text-slate-400 text-xs uppercase">
                <th className="text-left px-3 py-2">Case</th>
                <th className="text-left px-3 py-2">Model</th>
                <th className="text-left px-3 py-2">Baseline</th>
                <th className="text-left px-3 py-2">Passed</th>
                <th className="text-left px-3 py-2">Delta</th>
                <th className="text-left px-3 py-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {regression.items.map((item, i) => (
                <RegressionRow key={i} item={item} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
