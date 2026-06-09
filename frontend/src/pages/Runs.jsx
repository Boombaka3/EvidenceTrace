// frontend/src/pages/Runs.jsx
import { useNavigate } from 'react-router-dom'

export default function Runs() {
  const navigate = useNavigate()
  return (
    <div>
      <h1 className="text-xl font-semibold text-white mb-6">Runs</h1>
      <div className="border border-slate-700 bg-slate-900 px-6 py-10 text-center space-y-4">
        <p className="text-slate-400 text-sm">
          No runs list endpoint yet. Dispatch a new run to see it here.
        </p>
        <button
          onClick={() => navigate('/runs/new')}
          className="bg-indigo-500 hover:bg-indigo-600 text-white text-sm px-5 py-2 transition-colors"
        >
          + New Run
        </button>
      </div>
    </div>
  )
}
