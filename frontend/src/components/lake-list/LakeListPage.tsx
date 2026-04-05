import { useLakes } from '../../hooks/useLakes'
import { LakeCard } from './LakeCard'
import { LoadingSpinner } from '../shared/LoadingSpinner'

export function LakeListPage() {
  const { lakes, loading, error } = useLakes()

  if (loading) return <LoadingSpinner />

  if (error) {
    return (
      <div className="text-center p-8 text-red-600">
        <p className="text-lg font-semibold">Failed to load lakes</p>
        <p className="text-sm mt-1">{error}</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {lakes.map((lake) => (
        <LakeCard key={lake.lake_id} lake={lake} />
      ))}
    </div>
  )
}
