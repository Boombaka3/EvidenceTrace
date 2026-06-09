// frontend/src/App.jsx
import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout.jsx'
import Suites from './pages/Suites.jsx'
import Cases from './pages/Cases.jsx'
import NewRun from './pages/NewRun.jsx'
import Runs from './pages/Runs.jsx'
import RunStatus from './pages/RunStatus.jsx'
import Results from './pages/Results.jsx'

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Navigate to="/suites" replace />} />
        <Route path="/suites" element={<Suites />} />
        <Route path="/suites/:id" element={<Cases />} />
        <Route path="/runs/new" element={<NewRun />} />
        <Route path="/runs" element={<Runs />} />
        <Route path="/runs/:id" element={<RunStatus />} />
        <Route path="/runs/:id/results" element={<Results />} />
        <Route path="/models" element={
          <div className="text-slate-400 text-sm">Models info -- coming soon.</div>
        } />
      </Routes>
    </Layout>
  )
}
