import { useNavigate } from 'react-router-dom'

export function Header() {
  const navigate = useNavigate()
  return (
    <header className="bg-ocean-900 text-white shadow-md">
      <div className="max-w-5xl mx-auto px-4 py-4 flex items-center gap-3">
        <button onClick={() => navigate('/')} className="flex items-center gap-2 hover:opacity-80">
          <span className="text-2xl">🏄</span>
          <span className="text-xl font-bold tracking-tight">Wake Surf Weather</span>
        </button>
        <span className="ml-auto text-sm text-ocean-200">Utah Lakes</span>
      </div>
    </header>
  )
}
