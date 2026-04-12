import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useUserLocation } from '../../src/hooks/useUserLocation'

const STORAGE_KEY = 'sortByDistance'

function mockGeolocation(
  result: 'success' | 'error',
  coords = { latitude: 40.76, longitude: -111.89 },
) {
  const getCurrentPosition = vi.fn((onSuccess, onError) => {
    if (result === 'success') {
      onSuccess({ coords })
    } else {
      onError(new Error('permission denied'))
    }
  })
  Object.defineProperty(navigator, 'geolocation', {
    value: { getCurrentPosition },
    configurable: true,
  })
  return getCurrentPosition
}

beforeEach(() => {
  localStorage.clear()
  vi.restoreAllMocks()
})

describe('useUserLocation — initial state', () => {
  it('starts idle with no coords', () => {
    mockGeolocation('success')
    const { result } = renderHook(() => useUserLocation())
    expect(result.current.status).toBe('idle')
    expect(result.current.coords).toBeNull()
  })

  it('does not call geolocation on mount when localStorage flag is absent', () => {
    const spy = mockGeolocation('success')
    renderHook(() => useUserLocation())
    expect(spy).not.toHaveBeenCalled()
  })
})

describe('useUserLocation — request()', () => {
  it('transitions to granted and provides coords on success', async () => {
    mockGeolocation('success')
    const { result } = renderHook(() => useUserLocation())

    await act(() => { result.current.request() })

    expect(result.current.status).toBe('granted')
    expect(result.current.coords).toEqual({ lat: 40.76, lng: -111.89 })
  })

  it('persists the opt-in to localStorage on grant', async () => {
    mockGeolocation('success')
    const { result } = renderHook(() => useUserLocation())

    await act(() => { result.current.request() })

    expect(localStorage.getItem(STORAGE_KEY)).toBe('true')
  })

  it('transitions to denied on permission error', async () => {
    mockGeolocation('error')
    const { result } = renderHook(() => useUserLocation())

    await act(() => { result.current.request() })

    expect(result.current.status).toBe('denied')
    expect(result.current.coords).toBeNull()
  })

  it('removes localStorage flag on denial', async () => {
    localStorage.setItem(STORAGE_KEY, 'true')
    mockGeolocation('error')
    const { result } = renderHook(() => useUserLocation())

    await act(() => { result.current.request() })

    expect(localStorage.getItem(STORAGE_KEY)).toBeNull()
  })

  it('reports unavailable when navigator.geolocation is not supported', async () => {
    Object.defineProperty(navigator, 'geolocation', { value: undefined, configurable: true })
    const { result } = renderHook(() => useUserLocation())

    await act(() => { result.current.request() })

    expect(result.current.status).toBe('unavailable')
  })
})

describe('useUserLocation — auto-apply on mount', () => {
  it('auto-requests location when localStorage flag is set', async () => {
    localStorage.setItem(STORAGE_KEY, 'true')
    const spy = mockGeolocation('success')

    await act(async () => { renderHook(() => useUserLocation()) })

    expect(spy).toHaveBeenCalledOnce()
  })

  it('is granted immediately on mount when flag is set and permission was cached', async () => {
    localStorage.setItem(STORAGE_KEY, 'true')
    mockGeolocation('success')

    const { result } = await act(async () => renderHook(() => useUserLocation()))

    expect(result.current.status).toBe('granted')
  })
})

describe('useUserLocation — clear()', () => {
  it('resets status to idle and removes coords', async () => {
    mockGeolocation('success')
    const { result } = renderHook(() => useUserLocation())
    await act(() => { result.current.request() })

    act(() => { result.current.clear() })

    expect(result.current.status).toBe('idle')
    expect(result.current.coords).toBeNull()
  })

  it('removes the localStorage flag', async () => {
    mockGeolocation('success')
    const { result } = renderHook(() => useUserLocation())
    await act(() => { result.current.request() })

    act(() => { result.current.clear() })

    expect(localStorage.getItem(STORAGE_KEY)).toBeNull()
  })
})
