from __future__ import annotations

from .models import LatLng, PlaceInput


def format_location(place: PlaceInput) -> str:
  if place.place_id:
    return f"place_id:{place.place_id}"
  if not place.location:
    raise ValueError("Location missing for place")
  return f"{place.location.lat},{place.location.lng}"


def place_key(place: PlaceInput) -> str:
  if place.place_id:
    return f"place_id:{place.place_id}"
  if not place.location:
    raise ValueError("Location missing for place")
  return f"latlng:{place.location.lat:.6f},{place.location.lng:.6f}"


def _decode_varint(encoded: str, index: int) -> tuple[int, int]:
  shift = 0
  result = 0
  while True:
    if index >= len(encoded):
      raise ValueError("Invalid polyline encoding")
    byte = ord(encoded[index]) - 63
    index += 1
    result |= (byte & 0x1F) << shift
    shift += 5
    if byte < 0x20:
      break
  return (~(result >> 1) if (result & 1) else (result >> 1)), index


def decode_polyline(encoded: str) -> list[LatLng]:
  if not encoded:
    return []

  index = 0
  latitude = 0
  longitude = 0
  points: list[LatLng] = []

  while index < len(encoded):
    delta_lat, index = _decode_varint(encoded, index)
    latitude += delta_lat
    delta_lng, index = _decode_varint(encoded, index)
    longitude += delta_lng
    points.append(LatLng(lat=latitude / 1e5, lng=longitude / 1e5))

  return points


def compute_totals(
  order_indices: list[int],
  distance_matrix: list[list[float]],
  duration_matrix: list[list[float]],
  return_to_origin: bool,
) -> tuple[float, float]:
  total_distance = 0.0
  total_duration = 0.0

  for current_index, next_index in zip(order_indices, order_indices[1:]):
    total_distance += distance_matrix[current_index][next_index]
    total_duration += duration_matrix[current_index][next_index]

  if return_to_origin and order_indices:
    last_index = order_indices[-1]
    origin_index = order_indices[0]
    total_distance += distance_matrix[last_index][origin_index]
    total_duration += duration_matrix[last_index][origin_index]

  return total_distance, total_duration
