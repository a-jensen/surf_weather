import { useState } from 'react'
import type { SortOption } from '../utils/sorting'

const PREFS_KEY = 'preferences'
const VALID_SORTS: SortOption[] = ['default', 'name', 'temperature', 'conditions', 'distance']

interface StoredPreferences {
  pinnedLakes: string[]
  sortBy: SortOption
}

const DEFAULT_PREFS: StoredPreferences = { pinnedLakes: [], sortBy: 'default' }

function loadPrefs(): StoredPreferences {
  try {
    const raw = localStorage.getItem(PREFS_KEY)
    if (!raw) return DEFAULT_PREFS
    const parsed = JSON.parse(raw) as Partial<StoredPreferences>
    return {
      pinnedLakes: Array.isArray(parsed.pinnedLakes) ? parsed.pinnedLakes : [],
      sortBy: VALID_SORTS.includes(parsed.sortBy as SortOption)
        ? (parsed.sortBy as SortOption)
        : 'default',
    }
  } catch {
    return DEFAULT_PREFS
  }
}

export function usePreferences() {
  const [prefs, setPrefs] = useState<StoredPreferences>(loadPrefs)

  function save(next: StoredPreferences) {
    setPrefs(next)
    localStorage.setItem(PREFS_KEY, JSON.stringify(next))
  }

  function togglePin(lakeId: string) {
    const pinned = prefs.pinnedLakes.includes(lakeId)
      ? prefs.pinnedLakes.filter(id => id !== lakeId)
      : [...prefs.pinnedLakes, lakeId]
    save({ ...prefs, pinnedLakes: pinned })
  }

  function setSortBy(sortBy: SortOption) {
    save({ ...prefs, sortBy })
  }

  return { pinnedLakes: prefs.pinnedLakes, sortBy: prefs.sortBy, togglePin, setSortBy }
}
