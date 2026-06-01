import { useMemo, useState, type CSSProperties } from 'react'
import MapCanvas from '../components/MapCanvas'
import PlaceRow from '../components/PlaceRow'
import { useGoogleMaps } from '../hooks/useGoogleMaps'
import { optimizeRoute } from '../services/routeApi'
import type { OptimizeResponse, PlaceInput, PlaceSelection } from '../types/route'
import { createId } from '../utils/ids'
import { formatDistance, formatDuration } from '../utils/format'
import { findPairExceedingRadius } from '../utils/geo'

const MAX_PLACES = 15

const createEmptyPlace = (): PlaceInput => ({
  id: createId(),
  label: '',
  address: '',
})

const mapsApiKey = (import.meta.env.VITE_GOOGLE_MAPS_API_KEY ?? '') as string

export default function RouteOptimizerPage() {
  const [places, setPlaces] = useState<PlaceInput[]>(() => [
    createEmptyPlace(),
    createEmptyPlace(),
  ])
  const [returnToOrigin, setReturnToOrigin] = useState(true)
  const [route, setRoute] = useState<OptimizeResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const { status: mapsStatus, error: mapsError } = useGoogleMaps(mapsApiKey)
  const mapsReady = mapsStatus === 'ready'

  const validPlaces = useMemo(
    () => places.filter((place) => place.location && place.label.trim()),
    [places],
  )

  const orderedPlaces = useMemo(() => {
    if (!route?.order?.length) {
      return []
    }

    const byId = new Map(places.map((place) => [place.id, place]))
    return route.order
      .map((id) => byId.get(id))
      .filter(Boolean) as PlaceInput[]
  }, [places, route])

  const mapStatusMessage = mapsError
    ? mapsError
    : mapsStatus === 'loading'
      ? 'Cargando mapa de Google...'
      : 'Agrega tu API key para ver el mapa.'

  const handleAddPlace = () => {
    if (places.length >= MAX_PLACES) {
      return
    }

    setPlaces((prev) => [...prev, createEmptyPlace()])
    setRoute(null)
  }

  const handleRemovePlace = (id: string) => {
    setPlaces((prev) => prev.filter((place) => place.id !== id))
    setRoute(null)
  }

  const handleChangePlace = (id: string, label: string) => {
    setPlaces((prev) =>
      prev.map((place) =>
        place.id === id
          ? {
              ...place,
              label,
              address: '',
              placeId: undefined,
              location: undefined,
            }
          : place,
      ),
    )
    setRoute(null)
  }

  const handleSelectPlace = (id: string, payload: PlaceSelection) => {
    setPlaces((prev) =>
      prev.map((place) =>
        place.id === id
          ? {
              ...place,
              label: payload.label,
              address: payload.address,
              placeId: payload.placeId,
              location: payload.location,
            }
          : place,
      ),
    )
    setRoute(null)
  }

  const handleOptimize = async () => {
    setError(null)
    const payloadPlaces = validPlaces

    if (payloadPlaces.length < 2) {
      setError('Agrega al menos dos lugares validos antes de optimizar.')
      return
    }

    const overLimit = findPairExceedingRadius(
      payloadPlaces as Array<{ label: string; location: { lat: number; lng: number } }>,
    )
    if (overLimit) {
      setError(
        `"${overLimit.a}" y "${overLimit.b}" estan a ${overLimit.km} km entre si. El radio maximo permitido es 100 km.`,
      )
      return
    }

    setIsLoading(true)
    try {
      const result = await optimizeRoute({
        places: payloadPlaces,
        returnToOrigin,
      })
      setRoute(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error inesperado al optimizar.')
    } finally {
      setIsLoading(false)
    }
  }

  const canOptimize = validPlaces.length >= 2 && !isLoading
  const canRemove = places.length > 2

  return (
    <div className="app-shell">
      <header className="top-bar">
        <div className="brand">
          <div>
            <h1 className="title">Route Optimizer</h1>
          </div>
        </div>
      </header>

      <section className="layout">
        <aside className="panel">
          <div className="panel-head">
            <h2 className="panel-title">Lugares</h2>
            <p className="panel-sub">
              Usa el autocompletado para guardar coordenadas precisas.
            </p>
          </div>

          <div className="place-list">
            {places.map((place, index) => (
              <PlaceRow
                key={place.id}
                index={index}
                place={place}
                mapsReady={mapsReady}
                onChange={handleChangePlace}
                onSelect={handleSelectPlace}
                onRemove={handleRemovePlace}
                canRemove={canRemove}
              />
            ))}
          </div>

          <div className="row-actions">
            <button
              type="button"
              className="ghost-button"
              onClick={handleAddPlace}
              disabled={places.length >= MAX_PLACES}
            >
              + Agregar lugar
            </button>
            <span className="helper">
              {places.length}/{MAX_PLACES} lugares
            </span>
          </div>

          <div className="toggle-row">
            <span className="helper">Regresar al origen</span>
            <label className="toggle">
              <input
                type="checkbox"
                checked={returnToOrigin}
                onChange={(event) => setReturnToOrigin(event.target.checked)}
              />
              <span className="toggle-track">
                <span className="toggle-thumb" />
              </span>
            </label>
          </div>

          <button
            type="button"
            className="primary-button"
            onClick={handleOptimize}
            disabled={!canOptimize}
          >
            {isLoading ? 'Optimizando ruta...' : 'Optimizar ruta'}
          </button>

          {error && <div className="alert">{error}</div>}

          <div className="result-card">
            <h3 className="result-title">Mejor ruta</h3>
            {route && orderedPlaces.length > 0 ? (
              <ol className="route-list">
                {orderedPlaces.map((place, index) => (
                  <li
                    key={place.id}
                    style={{ '--delay': `${index * 0.05}s` } as CSSProperties}
                  >
                    {place.address || place.label}
                  </li>
                ))}
              </ol>
            ) : (
              <p className="empty-state">
                Ejecuta la optimizacion para ver el orden recomendado.
              </p>
            )}
          </div>
        </aside>

        <main className="map-panel">
          <MapCanvas
            places={validPlaces}
            route={route}
            mapsReady={mapsReady}
            statusMessage={mapStatusMessage}
          />
          <div className="map-overlay">
            <div className="stat-card">
              <div className="stat">
                <span className="stat-label">Distancia total</span>
                <span className="stat-value">
                  {route ? formatDistance(route.totalDistanceMeters) : '--'}
                </span>
              </div>
              <div className="stat">
                <span className="stat-label">Tiempo estimado</span>
                <span className="stat-value">
                  {route ? formatDuration(route.totalDurationSeconds) : '--'}
                </span>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat">
                <span className="stat-label">Lugares validos</span>
                <span className="stat-value">{validPlaces.length}</span>
              </div>
              <p className="map-hint">
                Usa el autocompletado para reducir errores y llamadas fallidas.
              </p>
            </div>
          </div>
        </main>
      </section>
    </div>
  )
}
