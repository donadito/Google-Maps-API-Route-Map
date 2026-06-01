const EARTH_RADIUS_KM = 6371

function toRad(deg: number): number {
  return (deg * Math.PI) / 180
}

export function haversineKm(
  lat1: number,
  lng1: number,
  lat2: number,
  lng2: number,
): number {
  const dLat = toRad(lat2 - lat1)
  const dLng = toRad(lng2 - lng1)
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLng / 2) ** 2
  return EARTH_RADIUS_KM * 2 * Math.asin(Math.sqrt(a))
}

/** Returns the first pair of places that exceed maxKm, or null if all are within range. */
export function findPairExceedingRadius(
  places: Array<{ label: string; location: { lat: number; lng: number } }>,
  maxKm = 100,
): { a: string; b: string; km: number } | null {
  for (let i = 0; i < places.length; i++) {
    for (let j = i + 1; j < places.length; j++) {
      const km = haversineKm(
        places[i].location.lat,
        places[i].location.lng,
        places[j].location.lat,
        places[j].location.lng,
      )
      if (km > maxKm) {
        return { a: places[i].label, b: places[j].label, km: Math.round(km) }
      }
    }
  }
  return null
}
