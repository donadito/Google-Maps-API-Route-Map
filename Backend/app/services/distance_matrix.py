from __future__ import annotations

import httpx

from .cache import DistanceCache
from .google_api import fetch_distance_row
from ..models import PlaceInput
from ..utils import place_key


def estimate_duration_matrix(
  distance_matrix: list[list[float]],
  speed_kmph: float,
) -> list[list[float]]:
  speed_mps = max(speed_kmph, 1.0) * 1000 / 3600
  return [[distance / speed_mps for distance in row] for row in distance_matrix]


async def build_distance_matrices(
  places: list[PlaceInput],
  api_key: str,
  cache: DistanceCache,
  client: httpx.AsyncClient,
) -> tuple[list[list[float]], list[list[float]]]:
  size = len(places)
  distance_matrix = [[0.0 for _ in range(size)] for _ in range(size)]
  duration_matrix = [[0.0 for _ in range(size)] for _ in range(size)]

  place_keys = [place_key(place) for place in places]
  missing: dict[int, list[int]] = {}

  for i in range(size):
    for j in range(size):
      if i == j:
        continue
      cached = cache.get(place_keys[i], place_keys[j])
      if cached:
        distance_matrix[i][j], duration_matrix[i][j] = cached
      else:
        missing.setdefault(i, []).append(j)

  for origin_index, destination_indices in missing.items():
    origin = places[origin_index]
    destinations = [places[j] for j in destination_indices]

    results = await fetch_distance_row(api_key, origin, destinations, client)
    cache_records: list[tuple[str, str, float, float]] = []

    for destination_index, (distance, duration) in zip(destination_indices, results):
      distance_matrix[origin_index][destination_index] = distance
      duration_matrix[origin_index][destination_index] = duration
      cache_records.append(
        (
          place_keys[origin_index],
          place_keys[destination_index],
          distance,
          duration,
        )
      )

    cache.set_many(cache_records)

  return distance_matrix, duration_matrix
