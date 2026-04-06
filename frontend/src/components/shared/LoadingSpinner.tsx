export function LoadingSpinner() {
  return (
    <div className="flex justify-center items-center p-8">
      <div
        className="w-10 h-10 border-4 border-ocean-200 border-t-ocean-600 rounded-full animate-spin"
        role="status"
        aria-label="Loading"
      />
    </div>
  )
}
