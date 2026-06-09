// frontend/src/components/Layout.jsx
import { NavLink } from 'react-router-dom'

const navItems = [
  { to: '/suites', label: 'Suites' },
  { to: '/runs/new', label: 'New Run' },
  { to: '/runs', label: 'Runs' },
]

export default function Layout({ children }) {
  return (
    <div className="flex min-h-screen bg-slate-900">
      {/* Sidebar */}
      <aside className="w-60 flex-shrink-0 fixed top-0 left-0 h-screen bg-slate-900 border-r border-slate-700 flex flex-col">
        <div className="px-5 pt-6 pb-4">
          <div className="font-mono font-bold text-white text-lg">Gauntlet</div>
          <div className="text-slate-400 text-xs mt-0.5">LLM Eval Harness</div>
        </div>

        <nav className="flex-1 px-3 space-y-0.5">
          {navItems.map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `block px-3 py-2 text-sm rounded-none transition-colors ${
                  isActive
                    ? 'text-indigo-400 bg-slate-800'
                    : 'text-slate-300 hover:text-white hover:bg-slate-800'
                }`
              }
            >
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="px-3 pb-6">
          <NavLink
            to="/models"
            className={({ isActive }) =>
              `block px-3 py-2 text-sm rounded-none transition-colors ${
                isActive
                  ? 'text-indigo-400 bg-slate-800'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              }`
            }
          >
            Models
          </NavLink>
        </div>
      </aside>

      {/* Main content */}
      <main className="ml-60 flex-1 min-h-screen bg-slate-950 p-6">
        {children}
      </main>
    </div>
  )
}
