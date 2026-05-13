import { useEffect, useRef } from 'react'
import type { OptimizeResponse, PlaceInput } from '../types/route'

type MapCanvasProps = {
  places: PlaceInput[]
  route: OptimizeResponse | null
  mapsReady: boolean
  statusMessage: string
}

const DEFAULT_CENTER = { lat: 14.6349, lng: -90.5069 }

export default function MapCanvas({
  places,
  route,
  mapsReady,
  statusMessage,
}: MapCanvasProps) {
  const mapRef = useRef<HTMLDivElement | null>(null)
  const mapInstance = useRef<google.maps.Map | null>(null)
  const markersRef = useRef<google.maps.Marker[]>([])
  const polylineRef = useRef<google.maps.Polyline | null>(null)

  useEffect(() => {
    if (!mapsReady || !mapRef.current || mapInstance.current) {
      return
    }

    mapInstance.current = new google.maps.Map(mapRef.current, {
      center: DEFAULT_CENTER,
      zoom: 12,
      mapTypeControl: false,
      fullscreenControl: false,
      streetViewControl: false,
      clickableIcons: false,
      gestureHandling: 'greedy',
    })
  }, [mapsReady])

  useEffect(() => {
    if (!mapInstance.current) {
      return
    }

    markersRef.current.forEach((marker) => marker.setMap(null))
    markersRef.current = []

    const validPlaces = places.filter((place) => place.location)
    if (validPlaces.length === 0) {
      return
    }

    const bounds = new google.maps.LatLngBounds()

    validPlaces.forEach((place, index) => {
      if (!place.location) {
        return
      }

      const marker = new google.maps.Marker({
        position: place.location,
        map: mapInstance.current ?? undefined,
        label: {
          text: `${index + 1}`,
          color: '#ffffff',
          fontWeight: '600',
        },
      })

      markersRef.current.push(marker)
      bounds.extend(place.location)
    })

    if (validPlaces.length === 1) {
      mapInstance.current.setCenter(validPlaces[0].location ?? DEFAULT_CENTER)
      mapInstance.current.setZoom(14)
    } else {
      mapInstance.current.fitBounds(bounds, 80)
    }
  }, [places, mapsReady])

  useEffect(() => {
    if (!mapInstance.current) {
      return
    }

    if (polylineRef.current) {
      polylineRef.current.setMap(null)
      polylineRef.current = null
    }

    if (!route?.polyline?.length) {
      return
    }

    polylineRef.current = new google.maps.Polyline({
      path: route.polyline,
      map: mapInstance.current,
      strokeColor: '#0f6c7a',
      strokeOpacity: 0.9,
      strokeWeight: 4,
    })

    const bounds = new google.maps.LatLngBounds()
    route.polyline.forEach((point) => bounds.extend(point))
    mapInstance.current.fitBounds(bounds, 80)
  }, [route, mapsReady])

  return (
    <div className="map-canvas">
      <div ref={mapRef} className="map-surface" />
      {!mapsReady && <div className="map-loading">{statusMessage}</div>}
    </div>
  )
}
