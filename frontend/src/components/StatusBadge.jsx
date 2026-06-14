// frontend/src/components/StatusBadge.jsx
// Linear status-badge spec: surface-2 bg, ink-muted text, rounded-full pill, caption typography
const STATUS_STYLES = {
  PENDING:    'bg-gauntlet-warning/10 text-gauntlet-warning border border-gauntlet-warning/20',
  DISPATCHED: 'bg-[#141516] text-[#d0d6e0] border border-[#23252a]',
  RUNNING:    'bg-gauntlet-accent/10 text-gauntlet-accent border border-gauntlet-accent/20 animate-pulse',
  DONE:       'bg-gauntlet-success/10 text-gauntlet-success border border-gauntlet-success/20',
  FAILED:     'bg-gauntlet-danger/10 text-gauntlet-danger border border-gauntlet-danger/20',
}

export default function StatusBadge({ status, size = 'sm' }) {
  const style = STATUS_STYLES[status] || 'bg-[#141516] text-[#8a8f98] border border-[#23252a]'
  const sz = size === 'lg' ? 'text-xs px-3 py-1' : 'text-xs px-2 py-0.5'
  return (
    <span className={`inline-block font-mono uppercase tracking-wider rounded-full ${sz} ${style}`}>
      {status}
    </span>
  )
}
