import { useState, useEffect } from 'react'
import { api } from '../api/client'
import type { LakeDetail } from '../api/types'

export function useLakeDetail(lakeId: string) {
  const [detail, setDetail] = useState<LakeDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!lakeId) return
    setLoading(true)
    setError(null)
    api.getLake(lakeId)
      .then(setDetail)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false))
  }, [lakeId])

  return { detail, loading, error }
}
