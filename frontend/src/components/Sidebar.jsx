// frontend/src/components/Sidebar.jsx
import { NavLink } from 'react-router-dom'

const GridIcon = () => (
  <svg width="15" height="15" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
    <rect x="1" y="1" width="6" height="6" rx="1" />
    <rect x="9" y="1" width="6" height="6" rx="1" />
    <rect x="1" y="9" width="6" height="6" rx="1" />
    <rect x="9" y="9" width="6" height="6" rx="1" />
  </svg>
)

const PlayIcon = () => (
  <svg width="15" height="15" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
    <path d="M4 2 L13 8 L4 14 Z" />
  </svg>
)

const ListIcon = () => (
  <svg width="15" height="15" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
    <rect x="2" y="2" width="12" height="2" rx="1" />
    <rect x="2" y="7" width="12" height="2" rx="1" />
    <rect x="2" y="12" width="12" height="2" rx="1" />
  </svg>
)

const ChipIcon = () => (
  <svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true">
    <rect x="4" y="4" width="8" height="8" rx="1" />
    <line x1="4" y1="2" x2="4" y2="4" />
    <line x1="8" y1="1" x2="8" y2="4" />
    <line x1="12" y1="2" x2="12" y2="4" />
    <line x1="14" y1="6" x2="12" y2="6" />
    <line x1="14" y1="10" x2="12" y2="10" />
    <line x1="12" y1="12" x2="12" y2="14" />
    <line x1="8" y1="12" x2="8" y2="15" />
    <line x1="4" y1="12" x2="4" y2="14" />
    <line x1="2" y1="6" x2="4" y2="6" />
    <line x1="2" y1="10" x2="4" y2="10" />
  </svg>
)

const NAV = [
  { to: '/suites',   label: 'Suites',   Icon: GridIcon },
  { to: '/runs/new', label: 'New Run',  Icon: PlayIcon },
  { to: '/runs',     label: 'Runs',     Icon: ListIcon },
  { to: '/models',   label: 'Models',   Icon: ChipIcon },
]

export default function Sidebar() {
  return (
    <aside className="w-60 flex-shrink-0 fixed top-0 left-0 h-screen
                      bg-gauntlet-surface border-r border-gauntlet-border
                      flex flex-col">
      {/* Brand */}
      <div className="px-5 pt-5 pb-4">
        <div className="flex items-center gap-2">
          {/* Linear-style logomark: small accent square */}
          <div className="w-5 h-5 rounded bg-gauntlet-accent flex-shrink-0" />
          <span className="font-semibold text-gauntlet-text text-sm tracking-tight">
            EvidenceTrace
          </span>
        </div>
        <div className="text-gauntlet-muted text-xs mt-1.5 ml-7">
          Conflict detection
        </div>
        <div className="h-px bg-gauntlet-border mt-4" />
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 pt-1 space-y-0.5">
        {NAV.map(({ to, label, Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-2.5 px-3 py-2 text-sm rounded-lg transition-colors ${
                isActive
                  ? 'bg-linear-surface2 text-gauntlet-text'
                  : 'text-gauntlet-muted hover:bg-linear-surface2 hover:text-gauntlet-text'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <span className={isActive ? 'text-gauntlet-accent' : 'text-gauntlet-muted'}>
                  <Icon />
                </span>
                {label}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-5 py-4 border-t border-gauntlet-border space-y-1">
        <div className="text-gauntlet-muted text-xs font-mono tracking-tight">v1.0.0</div>
        <a
          href="https://github.com/Boombaka3/Gauntlet"
          target="_blank"
          rel="noreferrer"
          className="text-gauntlet-muted text-xs hover:text-gauntlet-accent transition-colors"
        >
          github ↗
        </a>
      </div>
    </aside>
  )
}
