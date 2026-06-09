// frontend/src/components/StatusBadge.jsx
const STATUS_STYLES = {
  PENDING: 'bg-slate-500 text-slate-200',
  DISPATCHED: 'bg-blue-600 text-white',
  RUNNING: 'bg-amber-500 text-white animate-pulse',
  DONE: 'bg-green-600 text-white',
  FAILED: 'bg-red-600 text-white',
}

export default function StatusBadge({ status, large = false }) {
  const style = STATUS_STYLES[status] || 'bg-slate-600 text-slate-200'
  return (
    <span
      className={`inline-block font-mono uppercase px-2 py-0.5 ${
        large ? 'text-sm' : 'text-xs'
      } ${style}`}
    >
      {status}
    </span>
  )
}
