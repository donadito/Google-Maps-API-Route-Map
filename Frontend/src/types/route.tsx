export type LatLngLiteral = {
  lat: number
  lng: number
}

export type PlaceInput = {
  id: string
  label: string
  address: string
  placeId?: string
  location?: LatLngLiteral
}

export type PlaceSelection = {
  label: string
  address: string
  placeId?: string
  location: LatLngLiteral
}

export type OptimizePayload = {
  places: PlaceInput[]
  returnToOrigin: boolean
}

export type OptimizeResponse = {
  order: string[]
  totalDistanceMeters: number
  totalDurationSeconds: number
  polyline: LatLngLiteral[]
}
