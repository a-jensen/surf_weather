import { describe, it, expect, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { usePreferences } from '../../src/hooks/usePreferences'

const PREFS_KEY = 'preferences'

beforeEach(() => {
  localStorage.clear()
})

describe('usePreferences — initial state', () => {
  it('starts with empty pinnedLakes and default sort when localStorage is empty', () => {
    const { result } = renderHook(() => usePreferences())
    expect(result.current.pinnedLakes).toEqual([])
    expect(result.current.sortBy).toBe('default')
  })

  it('restores saved pinnedLakes and sortBy from localStorage', () => {
    localStorage.setItem(PREFS_KEY, JSON.stringify({ pinnedLakes: ['deer_creek'], sortBy: 'name' }))
    const { result } = renderHook(() => usePreferences())
    expect(result.current.pinnedLakes).toEqual(['deer_creek'])
    expect(result.current.sortBy).toBe('name')
  })

  it('falls back to defaults when localStorage contains malformed JSON', () => {
    localStorage.setItem(PREFS_KEY, 'not-json')
    const { result } = renderHook(() => usePreferences())
    expect(result.current.pinnedLakes).toEqual([])
    expect(result.current.sortBy).toBe('default')
  })

  it('falls back to default sortBy when stored value is unrecognized', () => {
    localStorage.setItem(PREFS_KEY, JSON.stringify({ pinnedLakes: [], sortBy: 'bogus_sort' }))
    const { result } = renderHook(() => usePreferences())
    expect(result.current.sortBy).toBe('default')
  })

  it('falls back to empty pinnedLakes when stored value is not an array', () => {
    localStorage.setItem(PREFS_KEY, JSON.stringify({ pinnedLakes: 'not-an-array', sortBy: 'name' }))
    const { result } = renderHook(() => usePreferences())
    expect(result.current.pinnedLakes).toEqual([])
  })
})

describe('usePreferences — togglePin', () => {
  it('adds a lake to pinnedLakes', () => {
    const { result } = renderHook(() => usePreferences())
    act(() => { result.current.togglePin('deer_creek') })
    expect(result.current.pinnedLakes).toContain('deer_creek')
  })

  it('removes an already-pinned lake', () => {
    localStorage.setItem(PREFS_KEY, JSON.stringify({ pinnedLakes: ['deer_creek'], sortBy: 'default' }))
    const { result } = renderHook(() => usePreferences())
    act(() => { result.current.togglePin('deer_creek') })
    expect(result.current.pinnedLakes).not.toContain('deer_creek')
  })

  it('persists the updated pin list to localStorage', () => {
    const { result } = renderHook(() => usePreferences())
    act(() => { result.current.togglePin('jordanelle') })
    const stored = JSON.parse(localStorage.getItem(PREFS_KEY)!)
    expect(stored.pinnedLakes).toContain('jordanelle')
  })

  it('can pin multiple lakes independently', () => {
    const { result } = renderHook(() => usePreferences())
    act(() => { result.current.togglePin('lake_a') })
    act(() => { result.current.togglePin('lake_b') })
    expect(result.current.pinnedLakes).toEqual(['lake_a', 'lake_b'])
  })
})

describe('usePreferences — setSortBy', () => {
  it('updates the sortBy value', () => {
    const { result } = renderHook(() => usePreferences())
    act(() => { result.current.setSortBy('name') })
    expect(result.current.sortBy).toBe('name')
  })

  it('persists the updated sort to localStorage', () => {
    const { result } = renderHook(() => usePreferences())
    act(() => { result.current.setSortBy('temperature') })
    const stored = JSON.parse(localStorage.getItem(PREFS_KEY)!)
    expect(stored.sortBy).toBe('temperature')
  })

  it('preserves pinned lakes when sort is changed', () => {
    const { result } = renderHook(() => usePreferences())
    act(() => { result.current.togglePin('deer_creek') })
    act(() => { result.current.setSortBy('conditions') })
    expect(result.current.pinnedLakes).toContain('deer_creek')
  })
})

describe('usePreferences — persistence round-trip', () => {
  it('restores both pinnedLakes and sortBy after remount', () => {
    const { result, rerender } = renderHook(() => usePreferences())
    act(() => { result.current.togglePin('bear_lake') })
    act(() => { result.current.setSortBy('distance') })

    // Simulate remount by forcing a new hook instance via rerender with a key change
    localStorage.setItem(PREFS_KEY, localStorage.getItem(PREFS_KEY)!) // no-op, just explicit
    const { result: result2 } = renderHook(() => usePreferences())
    expect(result2.current.pinnedLakes).toContain('bear_lake')
    expect(result2.current.sortBy).toBe('distance')

    // silence unused var warning
    void rerender
  })
})
