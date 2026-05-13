import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type KeyboardEvent,
} from 'react'
import type { PlaceInput, PlaceSelection } from '../types/route'

type PlaceRowProps = {
  index: number
  place: PlaceInput
  mapsReady: boolean
  onChange: (id: string, label: string) => void
  onSelect: (id: string, payload: PlaceSelection) => void
  onRemove: (id: string) => void
  canRemove: boolean
}

type SuggestionItem = {
  prediction: google.maps.places.PlacePrediction
  displayText: string
}

const MIN_QUERY_LEN = 2

function latLngToLiteral(loc: google.maps.LatLng | google.maps.LatLngLiteral): {
  lat: number
  lng: number
} {
  const lat = typeof loc.lat === 'function' ? loc.lat() : loc.lat
  const lng = typeof loc.lng === 'function' ? loc.lng() : loc.lng
  return { lat, lng }
}

export default function PlaceRow({
  index,
  place,
  mapsReady,
  onChange,
  onSelect,
  onRemove,
  canRemove,
}: PlaceRowProps) {
  const inputRef = useRef<HTMLInputElement | null>(null)
  const rowRef = useRef<HTMLDivElement | null>(null)
  const [suggestions, setSuggestions] = useState<SuggestionItem[]>([])
  const [searchError, setSearchError] = useState<string | null>(null)
  const [searching, setSearching] = useState(false)
  const searchRequestId = useRef(0)

  useEffect(() => {
    setSearchError(null)
  }, [place.label])

  useEffect(() => {
    const close = (event: MouseEvent) => {
      if (rowRef.current?.contains(event.target as Node)) {
        return
      }
      setSuggestions([])
    }
    document.addEventListener('mousedown', close)
    return () => document.removeEventListener('mousedown', close)
  }, [])

  const applyPrediction = useCallback(
    async (prediction: google.maps.places.PlacePrediction) => {
      setSearchError(null)
      setSearching(true)
      const myId = ++searchRequestId.current

      try {
        await google.maps.importLibrary('places')
        const placeInstance = prediction.toPlace()
        await placeInstance.fetchFields({
          fields: ['location', 'formattedAddress', 'displayName'],
        })

        if (myId !== searchRequestId.current) {
          return
        }

        const loc = placeInstance.location
        if (!loc) {
          setSearchError('Este lugar no tiene coordenadas. Elige otra opción.')
          return
        }

        onSelect(place.id, {
          label: placeInstance.displayName ?? prediction.text.text,
          address: placeInstance.formattedAddress ?? prediction.text.text,
          placeId: prediction.placeId,
          location: latLngToLiteral(loc),
        })
        setSuggestions([])
      } catch (err) {
        if (myId !== searchRequestId.current) {
          return
        }
        const message =
          err instanceof Error ? err.message : 'No se pudieron cargar los detalles del lugar.'
        setSearchError(message)
      } finally {
        if (myId === searchRequestId.current) {
          setSearching(false)
        }
      }
    },
    [onSelect, place.id],
  )

  const runSearch = useCallback(async () => {
    if (!mapsReady) {
      return
    }

    const query = place.label.trim()
    if (query.length < MIN_QUERY_LEN) {
      setSearchError(`Escribe al menos ${MIN_QUERY_LEN} caracteres y pulsa Enter.`)
      setSuggestions([])
      return
    }

    setSearchError(null)
    setSearching(true)
    const myId = ++searchRequestId.current

    try {
      const places = (await google.maps.importLibrary(
        'places',
      )) as google.maps.PlacesLibrary

      const sessionToken = new places.AutocompleteSessionToken()
      const { suggestions: raw } =
        await places.AutocompleteSuggestion.fetchAutocompleteSuggestions({
          input: query,
          sessionToken,
          language: navigator.language,
        })

      if (myId !== searchRequestId.current) {
        return
      }

      const items: SuggestionItem[] = []
      for (const s of raw) {
        const prediction = s.placePrediction
        if (!prediction) {
          continue
        }
        items.push({
          prediction,
          displayText: prediction.text.text,
        })
      }

      if (items.length === 0) {
        setSuggestions([])
        setSearchError('No se encontraron coincidencias. Prueba otras palabras.')
        return
      }

      if (items.length === 1) {
        setSuggestions([])
        await applyPrediction(items[0].prediction)
        return
      }

      setSuggestions(items)
    } catch (err) {
      if (myId !== searchRequestId.current) {
        return
      }
      const message =
        err instanceof Error ? err.message : 'Error al buscar en Places.'
      setSearchError(message)
      setSuggestions([])
    } finally {
      if (myId === searchRequestId.current) {
        setSearching(false)
      }
    }
  }, [applyPrediction, mapsReady, place.label])

  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Escape') {
      setSuggestions([])
      setSearchError(null)
      return
    }
    if (event.key !== 'Enter') {
      return
    }
    event.preventDefault()
    void runSearch()
  }

  return (
    <div ref={rowRef} className={`place-row ${place.location ? 'ready' : ''}`}>
      <span className="place-index">{index + 1}</span>
      <div className="place-field">
        <input
          ref={inputRef}
          className="place-input"
          placeholder={`Lugar ${index + 1} — Enter para buscar`}
          value={place.label}
          onChange={(event) => onChange(place.id, event.target.value)}
          onKeyDown={handleKeyDown}
          autoComplete="off"
          aria-label={`Lugar ${index + 1}`}
          aria-expanded={suggestions.length > 0}
          aria-controls={`place-suggest-${place.id}`}
          disabled={searching}
        />
        {searchError && <p className="place-search-error">{searchError}</p>}
        {suggestions.length > 0 && (
          <ul
            id={`place-suggest-${place.id}`}
            className="place-suggestions"
            role="listbox"
            aria-label="Sugerencias de lugar"
          >
            {suggestions.map((item) => (
              <li key={item.prediction.placeId} role="none">
                <button
                  type="button"
                  role="option"
                  className="place-suggestion-item"
                  onClick={() => void applyPrediction(item.prediction)}
                >
                  {item.displayText}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
      <span className="place-status" aria-hidden="true" />
      <button
        type="button"
        className="icon-button"
        onClick={() => onRemove(place.id)}
        disabled={!canRemove}
        aria-label="Quitar lugar"
      >
        x
      </button>
    </div>
  )
}
