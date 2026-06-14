// frontend/src/pages/Results.jsx
import { useParams, Link } from 'react-router-dom'
import { useApi } from '../hooks/useApi.js'
import { getRunResults } from '../api/client.js'
import { MOCK_RESULTS } from '../data/mockData.js'
import { MockBanner } from '../components/MockBanner.jsx'
import { LoadingState } from '../components/LoadingState.jsx'
import { ErrorState } from '../components/ErrorState.jsx'
import ScoreBar from '../components/ScoreBar.jsx'
import ModelCompare from '../components/ModelCompare.jsx'
import DeltaBadge from '../components/DeltaBadge.jsx'

function StatCard({ label, value }) {
  return (
    <div className="bg-gauntlet-surface border border-gauntlet-border rounded-xl px-5 py-4">
      <div className="text-2xl font-bold text-gauntlet-text font-mono tracking-tight">{value}</div>
      <div className="text-gauntlet-muted text-xs mt-1">{label}</div>
    </div>
  )
}

export default function Results() {
  const { id } = useParams()
  const { data: results, loading, error, isMock, refetch } = useApi(
    () => getRunResults(id),
    MOCK_RESULTS,
    [id]
  )

  const passed = results ? results.filter(r => r.passed === true).length : 0
  const total = results ? results.length : 0
  const passRate = total > 0 ? Math.round((passed / total) * 100) + '%' : '--'
  const overallVals = results ? results.map(r => r.overall).filter(v => v != null) : []
  const avgScore = overallVals.length > 0
    ? (overallVals.reduce((a, b) => a + b, 0) / overallVals.length).toFixed(2)
    : '--'
  const modelCount = results
    ? [...new Set(results.map(r => r.model_id || r.model_run_id))].length
    : '--'

  const hasRegression = results && results.some(r => r.regression_delta != null)

  const byCaseId = {}
  if (results) {
    for (const r of results) {
      const key = r.prompt_case_id
      if (!byCaseId[key]) byCaseId[key] = []
      byCaseId[key].push(r)
    }
  }

  return (
    <div className="min-h-screen bg-gauntlet-bg">
      {isMock && <MockBanner />}
      <div className="px-8 py-8">
        <div className="mb-8">
          <Link to={`/runs/${id}`} className="text-gauntlet-muted hover:text-gauntlet-text text-xs font-mono transition-colors">
            ← Run #{id}
          </Link>
          <h1 className="text-xl font-semibold text-gauntlet-text tracking-tight mt-3">Results</h1>
        </div>

        {loading && <LoadingState rows={6} />}
        {error && <ErrorState message={error} onRetry={refetch} />}

        {!loading && !error && results && (
          <div className="space-y-8">
            {/* Stats grid */}
            <div className="grid grid-cols-4 gap-3">
              <StatCard label="Total results" value={total} />
              <StatCard label="Models tested" value={modelCount} />
              <StatCard label="Avg score" value={avgScore} />
              <StatCard label="Pass rate" value={passRate} />
            </div>

            {/* Model comparison */}
            {results.length > 0 && (
              <div className="bg-gauntlet-surface border border-gauntlet-border rounded-xl p-6">
                <ModelCompare results={results} />
              </div>
            )}

            {/* Results by case */}
            {Object.entries(byCaseId).map(([caseId, rows]) => (
              <div key={caseId}>
                <div className="text-gauntlet-muted text-xs font-mono uppercase tracking-wider mb-3">
                  Case #{caseId}
                </div>
                <div className="rounded-xl border border-gauntlet-border overflow-hidden">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-gauntlet-surface border-b border-gauntlet-border">
                        <th className="text-left px-5 py-3 text-gauntlet-muted text-xs font-medium uppercase tracking-wider">Model</th>
                        <th className="text-left px-5 py-3 text-gauntlet-muted text-xs font-medium uppercase tracking-wider">Score</th>
                        <th className="text-left px-5 py-3 text-gauntlet-muted text-xs font-medium uppercase tracking-wider">Passed</th>
                        <th className="text-left px-5 py-3 text-gauntlet-muted text-xs font-medium uppercase tracking-wider">Latency</th>
                        <th className="text-left px-5 py-3 text-gauntlet-muted text-xs font-medium uppercase tracking-wider">Delta</th>
                      </tr>
                    </thead>
                    <tbody>
                      {rows.map(r => (
                        <tr key={r.id} className="border-b border-gauntlet-border last:border-0 hover:bg-gauntlet-surface transition-colors">
                          <td className="px-5 py-3.5 font-mono text-sm text-gauntlet-text">
                            {r.model_id || `run #${r.model_run_id}`}
                          </td>
                          <td className="px-5 py-3.5">
                            <ScoreBar value={r.overall} />
                          </td>
                          <td className="px-5 py-3.5 font-bold text-base">
                            {r.passed === null || r.passed === undefined ? (
                              <span className="text-gauntlet-muted text-xs">--</span>
                            ) : r.passed ? (
                              <span className="text-gauntlet-success">✓</span>
                            ) : (
                              <span className="text-gauntlet-danger">✗</span>
                            )}
                          </td>
                          <td className="px-5 py-3.5 font-mono text-xs text-gauntlet-muted">
                            {r.latency_ms != null ? `${r.latency_ms}ms` : '--'}
                          </td>
                          <td className="px-5 py-3.5">
                            <DeltaBadge delta={r.regression_delta} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ))}

            {/* Regression section */}
            {hasRegression && (
              <div className="bg-gauntlet-surface border border-gauntlet-border rounded-xl p-6">
                <div className="text-gauntlet-text font-medium text-sm mb-4">Regression Summary</div>
                <div className="grid grid-cols-3 gap-3 text-xs font-mono">
                  <div className="bg-gauntlet-bg border border-gauntlet-border rounded-lg p-3">
                    <div className="text-gauntlet-success text-lg font-bold">
                      {results.filter(r => r.regression_delta > 0).length}
                    </div>
                    <div className="text-gauntlet-muted mt-1">Improved</div>
                  </div>
                  <div className="bg-gauntlet-bg border border-gauntlet-border rounded-lg p-3">
                    <div className="text-gauntlet-danger text-lg font-bold">
                      {results.filter(r => r.regression_delta < 0).length}
                    </div>
                    <div className="text-gauntlet-muted mt-1">Regressed</div>
                  </div>
                  <div className="bg-gauntlet-bg border border-gauntlet-border rounded-lg p-3">
                    <div className="text-gauntlet-muted text-lg font-bold">
                      {results.filter(r => r.regression_delta === 0 || r.regression_delta == null).length}
                    </div>
                    <div className="text-gauntlet-muted mt-1">Unchanged / N/A</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
