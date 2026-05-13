export function formatDistance(meters: number): string {
  if (!Number.isFinite(meters)) {
    return '--'
  }

  if (meters < 1000) {
    return `${Math.round(meters)} m`
  }

  return `${(meters / 1000).toFixed(1)} km`
}

export function formatDuration(seconds: number): string {
  if (!Number.isFinite(seconds)) {
    return '--'
  }

  const minutes = Math.round(seconds / 60)
  if (minutes < 60) {
    return `${minutes} min`
  }

  const hours = Math.floor(minutes / 60)
  const remainder = minutes % 60
  return `${hours} h ${remainder} min`
}
