import { useEffect, useState } from 'react'
import { loadGoogleMaps } from '../services/googleMaps'

type GoogleMapsStatus = 'idle' | 'loading' | 'ready' | 'error'

type GoogleMapsState = {
  status: GoogleMapsStatus
  error: string | null
}

export function useGoogleMaps(apiKey: string): GoogleMapsState {
  const [state, setState] = useState<GoogleMapsState>({
    status: 'idle',
    error: null,
  })

  useEffect(() => {
    if (!apiKey) {
      setState({
        status: 'error',
        error: 'Falta la API key de Google Maps.',
      })
      return
    }

    setState({ status: 'loading', error: null })
    loadGoogleMaps(apiKey)
      .then(() => setState({ status: 'ready', error: null }))
      .catch((err) => {
        setState({
          status: 'error',
          error: err instanceof Error ? err.message : 'No se pudo cargar el mapa.',
        })
      })
  }, [apiKey])

  return state
}
