// frontend/src/components/ProgressBar.jsx
export default function ProgressBar({ current, total }) {
  const pct = total > 0 ? Math.round((current / total) * 100) : 0

  return (
    <div>
      <div className="flex justify-between text-xs text-slate-400 font-mono mb-1">
        <span>{current} / {total}</span>
        <span>{pct}%</span>
      </div>
      <div className="w-full h-1.5 bg-slate-700">
        <div
          className="h-1.5 bg-indigo-500 transition-all duration-300"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}
