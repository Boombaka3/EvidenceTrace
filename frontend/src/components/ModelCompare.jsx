// frontend/src/components/ModelCompare.jsx
import ScoreBar from './ScoreBar.jsx'

export default function ModelCompare({ results }) {
  const sorted = [...results].sort((a, b) => {
    const av = a.overall ?? -1
    const bv = b.overall ?? -1
    return bv - av
  })

  return (
    <table className="w-full text-sm text-slate-200 border border-slate-700">
      <thead>
        <tr className="bg-slate-800 text-slate-400 text-xs uppercase">
          <th className="text-left px-3 py-2">Model</th>
          <th className="text-left px-3 py-2 w-40">Score</th>
          <th className="text-left px-3 py-2">Passed</th>
          <th className="text-left px-3 py-2">Latency</th>
          <th className="text-left px-3 py-2">Regression</th>
        </tr>
      </thead>
      <tbody>
        {sorted.map((r) => {
          const delta = r.regression_delta
          return (
            <tr key={r.id} className="border-t border-slate-700 hover:bg-slate-800">
              <td className="px-3 py-2 font-mono text-xs">{r.model_id || '--'}</td>
              <td className="px-3 py-2">
                <ScoreBar value={r.overall} width="120px" />
              </td>
              <td className="px-3 py-2">
                {r.passed === null || r.passed === undefined ? '--' : r.passed ? (
                  <span className="text-green-400">&#10003;</span>
                ) : (
                  <span className="text-red-400">&#10007;</span>
                )}
              </td>
              <td className="px-3 py-2 font-mono text-xs">
                {r.latency_ms != null ? `${r.latency_ms}ms` : '--'}
              </td>
              <td className="px-3 py-2 font-mono text-xs">
                {delta == null ? '--' : delta > 0 ? (
                  <span className="text-green-400">+{delta.toFixed(2)}</span>
                ) : delta < 0 ? (
                  <span className="text-red-400">{delta.toFixed(2)}</span>
                ) : (
                  <span className="text-slate-400">0.00</span>
                )}
              </td>
            </tr>
          )
        })}
      </tbody>
    </table>
  )
}
