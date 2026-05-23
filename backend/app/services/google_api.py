from __future__ import annotations

import httpx

from ..models import LatLng, PlaceInput
from ..utils import decode_polyline, format_location

DISTANCE_MATRIX_URL = "https://maps.googleapis.com/maps/api/distancematrix/json"
DIRECTIONS_URL = "https://maps.googleapis.com/maps/api/directions/json"


async def fetch_distance_row(
  api_key: str,
  origin: PlaceInput,
  destinations: list[PlaceInput],
  client: httpx.AsyncClient,
) -> list[tuple[float, float]]:
  if not destinations:
    return []

  params = {
    "origins": format_location(origin),
    "destinations": "|".join(format_location(dest) for dest in destinations),
    "key": api_key,
    "mode": "driving",
    "units": "metric",
  }

  response = await client.get(DISTANCE_MATRIX_URL, params=params)

  response.raise_for_status()
  payload = response.json()

  status = payload.get("status")
  if status != "OK":
    raise RuntimeError(f"Google API error: {status}")

  rows = payload.get("rows", [])
  if not rows:
    raise RuntimeError("Google API error: empty response rows")

  elements = rows[0].get("elements", [])
  if len(elements) != len(destinations):
    raise RuntimeError("Google API error: element count mismatch")

  results: list[tuple[float, float]] = []
  for element in elements:
    element_status = element.get("status")
    if element_status != "OK":
      raise RuntimeError(f"Google API element error: {element_status}")

    distance = float(element["distance"]["value"])
    duration = float(element["duration"]["value"])
    results.append((distance, duration))

  return results


async def fetch_directions_polyline(
  api_key: str,
  places: list[PlaceInput],
  order_indices: list[int],
  return_to_origin: bool,
  client: httpx.AsyncClient,
) -> list[LatLng]:
  if len(order_indices) < 2:
    return []

  ordered_places = [places[index] for index in order_indices]
  origin = format_location(ordered_places[0])

  if return_to_origin:
    destination = origin
    waypoint_places = ordered_places[1:]
  else:
    destination = format_location(ordered_places[-1])
    waypoint_places = ordered_places[1:-1]

  params = {
    "origin": origin,
    "destination": destination,
    "key": api_key,
    "mode": "driving",
    "units": "metric",
  }

  if waypoint_places:
    params["waypoints"] = "|".join(format_location(place) for place in waypoint_places)

  response = await client.get(DIRECTIONS_URL, params=params)

  response.raise_for_status()
  payload = response.json()

  status = payload.get("status")
  if status != "OK":
    raise RuntimeError(f"Google Directions error: {status}")

  routes = payload.get("routes", [])
  if not routes:
    raise RuntimeError("Google Directions error: no routes returned")

  overview = routes[0].get("overview_polyline", {})
  points = overview.get("points")
  if not points:
    raise RuntimeError("Google Directions error: missing polyline")

  return decode_polyline(points)
