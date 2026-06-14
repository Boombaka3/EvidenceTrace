// frontend/src/pages/Runs.jsx
import { Link } from 'react-router-dom'

export default function Runs() {
  return (
    <div className="min-h-screen bg-gauntlet-bg px-8 py-8">
      <div className="mb-8">
        <h1 className="text-xl font-semibold text-gauntlet-text tracking-tight">Runs</h1>
        <p className="text-gauntlet-muted text-sm mt-1">Evaluation run history</p>
      </div>

      <div className="bg-gauntlet-surface border border-gauntlet-border rounded-xl px-8 py-10 text-center max-w-sm">
        <div className="w-10 h-10 rounded-xl bg-gauntlet-border/50 flex items-center justify-center mx-auto mb-4">
          <svg width="18" height="18" viewBox="0 0 16 16" fill="currentColor" className="text-gauntlet-muted">
            <rect x="2" y="2" width="12" height="2" rx="1" />
            <rect x="2" y="7" width="12" height="2" rx="1" />
            <rect x="2" y="12" width="12" height="2" rx="1" />
          </svg>
        </div>
        <div className="text-gauntlet-text text-sm font-medium mb-1">No run list available</div>
        <p className="text-gauntlet-muted text-xs mb-6 leading-relaxed">
          Navigate directly to a run by ID, or dispatch a new run from any suite.
        </p>
        <Link
          to="/runs/new"
          className="inline-block bg-gauntlet-accent hover:bg-[#828fff] text-white text-sm font-medium px-5 py-2 rounded-lg transition-colors"
        >
          + New Run
        </Link>
      </div>
    </div>
  )
}
