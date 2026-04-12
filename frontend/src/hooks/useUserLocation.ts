import { useCallback, useEffect, useState } from 'react'

export type LocationStatus = 'idle' | 'loading' | 'granted' | 'denied' | 'unavailable'

export interface UserLocation {
  status: LocationStatus
  coords: { lat: number; lng: number } | null
  request: () => void
  clear: () => void
}

const STORAGE_KEY = 'sortByDistance'

export function useUserLocation(): UserLocation {
  const [status, setStatus] = useState<LocationStatus>('idle')
  const [coords, setCoords] = useState<{ lat: number; lng: number } | null>(null)

  const fetch = useCallback(() => {
    if (!navigator.geolocation) {
      setStatus('unavailable')
      return
    }
    setStatus('loading')
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setCoords({ lat: pos.coords.latitude, lng: pos.coords.longitude })
        setStatus('granted')
        localStorage.setItem(STORAGE_KEY, 'true')
      },
      () => {
        setStatus('denied')
        localStorage.removeItem(STORAGE_KEY)
      },
    )
  }, [])

  // Auto-apply on mount if the user previously opted in
  useEffect(() => {
    if (localStorage.getItem(STORAGE_KEY) === 'true') {
      fetch()
    }
  }, [fetch])

  const clear = useCallback(() => {
    setStatus('idle')
    setCoords(null)
    localStorage.removeItem(STORAGE_KEY)
  }, [])

  return { status, coords, request: fetch, clear }
}
