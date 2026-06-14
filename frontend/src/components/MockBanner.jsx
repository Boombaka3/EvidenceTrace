// frontend/src/components/MockBanner.jsx
export function MockBanner() {
  return (
    <div className="w-full bg-gauntlet-warning/10 border-b border-gauntlet-warning/20
                    px-6 py-2 flex items-center gap-2">
      <span className="w-1.5 h-1.5 rounded-full bg-gauntlet-warning animate-pulse flex-shrink-0" />
      <span className="text-gauntlet-warning text-xs font-mono tracking-tight">
        DEMO MODE — API unavailable. Showing sample data.
      </span>
    </div>
  )
}
