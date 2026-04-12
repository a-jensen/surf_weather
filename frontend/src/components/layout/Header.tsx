import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { SCORE_COLORS, type ConditionScoreValue } from '../../utils/lakeConditionScore'

const LEGEND_ITEMS: { score: ConditionScoreValue; lines: string[] }[] = [
  {
    score: 'Good',
    lines: ['Wind < 15 mph', 'Rain < 30%', 'No storm risk'],
  },
  {
    score: 'Fair',
    lines: ['Wind 15–21 mph', 'or Rain 30–59%'],
  },
  {
    score: 'Poor',
    lines: ['Wind ≥ 22 mph', 'Rain ≥ 60%', 'or Thunderstorm risk'],
  },
]

export function Header() {
  const navigate = useNavigate()
  const [legendOpen, setLegendOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!legendOpen) return
    function handleClick(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setLegendOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [legendOpen])

  return (
    <header className="bg-ocean-900 text-white shadow-md">
      <div className="max-w-5xl mx-auto px-4 py-4 flex items-center gap-3">
        <button onClick={() => navigate('/')} className="flex items-center gap-2 hover:opacity-80">
          <span className="text-2xl">🏄</span>
          <span className="text-xl font-bold tracking-tight">Wake Surf Weather</span>
        </button>

        <div className="ml-auto relative" ref={dropdownRef}>
          <button
            onClick={() => setLegendOpen(o => !o)}
            className="flex items-center gap-1 text-sm text-ocean-200 hover:text-white transition-colors"
          >
            Legend
            <svg
              className={`w-3.5 h-3.5 transition-transform ${legendOpen ? 'rotate-180' : ''}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2.5}
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {legendOpen && (
            <div className="absolute right-0 top-full mt-2 w-52 bg-white rounded-lg shadow-lg p-4 z-50">
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
                Forecast conditions
              </p>
              <div className="space-y-3">
                {LEGEND_ITEMS.map(({ score, lines }) => (
                  <div key={score} className="flex items-start gap-2.5">
                    <span className={`shrink-0 inline-block px-2 py-0.5 rounded text-xs font-medium mt-0.5 ${SCORE_COLORS[score]}`}>
                      {score}
                    </span>
                    <div className="text-xs text-gray-600 leading-relaxed">
                      {lines.map((line, i) => (
                        <div key={i}>{line}</div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
