// frontend/src/components/ScoreBar.jsx
export default function ScoreBar({ value, width = '100%' }) {
  if (value === null || value === undefined) {
    return <span className="text-slate-500 font-mono text-xs">N/A</span>
  }

  const pct = Math.round(value * 100)
  const fillColor =
    value >= 0.8 ? 'bg-green-500' : value >= 0.5 ? 'bg-amber-500' : 'bg-red-500'

  return (
    <div style={{ width }}>
      <div className="w-full h-2 bg-slate-700">
        <div
          className={`h-2 ${fillColor} transition-all`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <div className="text-xs font-mono text-slate-300 mt-0.5">
        {value.toFixed(2)}
      </div>
    </div>
  )
}
