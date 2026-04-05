import type { LakeDetail, LakeSummary } from './types'

const BASE = '/api'

async function get<T>(path: string): Promise<T> {
  const resp = await fetch(`${BASE}${path}`)
  if (!resp.ok) {
    throw new Error(`HTTP ${resp.status} — ${path}`)
  }
  return resp.json() as Promise<T>
}

export const api = {
  getLakes: (): Promise<LakeSummary[]> => get('/lakes'),
  getLake: (id: string): Promise<LakeDetail> => get(`/lakes/${id}`),
}
