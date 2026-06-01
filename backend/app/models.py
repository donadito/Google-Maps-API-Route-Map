import math
from pydantic import BaseModel, Field, ConfigDict, model_validator

_EARTH_RADIUS_KM = 6371.0


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
  d_lat = math.radians(lat2 - lat1)
  d_lng = math.radians(lng2 - lng1)
  a = math.sin(d_lat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lng / 2) ** 2
  return _EARTH_RADIUS_KM * 2 * math.asin(math.sqrt(a))


class LatLng(BaseModel):
  model_config = ConfigDict(frozen=True)

  lat: float
  lng: float


class PlaceInput(BaseModel):
  model_config = ConfigDict(populate_by_name=True)

  id: str
  label: str = ""
  address: str = ""
  place_id: str | None = Field(default=None, alias="placeId")
  location: LatLng | None = None


class OptimizeRequest(BaseModel):
  model_config = ConfigDict(populate_by_name=True)

  places: list[PlaceInput]
  return_to_origin: bool = Field(default=True, alias="returnToOrigin")
  weight_matrix: list[list[float]] | None = Field(default=None, alias="weightMatrix")
  duration_matrix: list[list[float]] | None = Field(
    default=None,
    alias="durationMatrix",
  )

  @staticmethod
  def _validate_square_matrix(matrix: list[list[float]], count: int, name: str) -> None:
    if len(matrix) != count:
      raise ValueError(f"La matriz de {name} no coincide con los lugares.")
    for row in matrix:
      if len(row) != count:
        raise ValueError(f"La matriz de {name} debe ser cuadrada.")

  @model_validator(mode="after")
  def validate_request(self):
    count = len(self.places)
    if count < 2:
      raise ValueError("Se requieren al menos 2 lugares.")
    if count > 15:
      raise ValueError("El maximo es 15 lugares.")

    located = [p for p in self.places if p.location is not None]
    for i in range(len(located)):
      for j in range(i + 1, len(located)):
        km = _haversine_km(
          located[i].location.lat, located[i].location.lng,
          located[j].location.lat, located[j].location.lng,
        )
        if km > 100:
          raise ValueError(
            f'"{located[i].label}" y "{located[j].label}" estan a {km:.0f} km entre si. El radio maximo es 100 km.'
          )

    if self.weight_matrix is not None:
      self._validate_square_matrix(self.weight_matrix, count, "pesos")
    if self.duration_matrix is not None:
      self._validate_square_matrix(self.duration_matrix, count, "duracion")

    return self


class OptimizeResponse(BaseModel):
  order: list[str]
  total_distance_meters: int = Field(..., alias="totalDistanceMeters")
  total_duration_seconds: int = Field(..., alias="totalDurationSeconds")
  polyline: list[LatLng]
