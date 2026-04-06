import { useState, useEffect } from 'react'
import { api } from '../api/client'
import type { LakeSummary } from '../api/types'

export function useLakes() {
  const [lakes, setLakes] = useState<LakeSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.getLakes()
      .then(setLakes)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  return { lakes, loading, error }
}
