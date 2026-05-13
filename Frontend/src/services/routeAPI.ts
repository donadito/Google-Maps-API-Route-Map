import type { OptimizePayload, OptimizeResponse } from '../types/route'

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000').replace(
  /\/$/,
  '',
)

export async function optimizeRoute(
  payload: OptimizePayload,
): Promise<OptimizeResponse> {
  const response = await fetch(`${API_BASE_URL}/optimize`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    const message = await response.text()
    throw new Error(message || 'No se pudo optimizar la ruta.')
  }

  return (await response.json()) as OptimizeResponse
}
