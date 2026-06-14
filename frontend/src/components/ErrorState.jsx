// frontend/src/components/ErrorState.jsx
export function ErrorState({ message, onRetry }) {
  return (
    <div className="flex flex-col items-center justify-center py-24 gap-4">
      <div className="w-10 h-10 rounded-xl bg-gauntlet-danger/10 border border-gauntlet-danger/20
                      flex items-center justify-center">
        <span className="text-gauntlet-danger text-lg font-bold font-mono">!</span>
      </div>
      <p className="text-gauntlet-text font-medium text-sm">Something went wrong</p>
      <p className="text-gauntlet-muted text-xs font-mono max-w-md text-center break-all">
        {message}
      </p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-2 px-4 py-2 rounded-lg border border-gauntlet-border
                     text-gauntlet-muted hover:text-gauntlet-text
                     hover:border-gauntlet-accent text-xs font-medium transition-colors"
        >
          Try again
        </button>
      )}
    </div>
  )
}
