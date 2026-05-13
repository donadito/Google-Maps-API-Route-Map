let loaderPromise: Promise<void> | null = null

type GoogleWindow = Window & {
  google?: typeof google
}

export function loadGoogleMaps(apiKey: string): Promise<void> {
  if (typeof window === 'undefined') {
    return Promise.reject(new Error('Google Maps can only load in the browser.'))
  }

  const currentWindow = window as GoogleWindow
  if (currentWindow.google?.maps) {
    return Promise.resolve()
  }

  if (loaderPromise) {
    return loaderPromise
  }

  loaderPromise = new Promise((resolve, reject) => {
    const script = document.createElement('script')
    const libraries = 'places,geometry'
    script.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(
      apiKey,
    )}&libraries=${libraries}&v=weekly`
    script.async = true
    script.defer = true
    script.onload = () => resolve()
    script.onerror = () => reject(new Error('Failed to load Google Maps.'))
    document.head.appendChild(script)
  })

  return loaderPromise
}
