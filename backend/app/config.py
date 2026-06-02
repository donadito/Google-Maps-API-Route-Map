import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


def _env_list(name: str, default: str = "") -> list[str]:
  raw = os.getenv(name, default)
  return [item.strip() for item in raw.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
  google_maps_api_key: str
  firebase_credentials_path: str
  firebase_project_id: str
  cache_db_path: str
  ga_population: int
  ga_generations: int
  ga_mutation_rate: float
  ga_elite_rate: float
  ga_tournament_size: int
  ga_seed: int | None
  default_speed_kmph: float
  cors_origins: list[str]
  allowed_client_ips: list[str]


def get_settings() -> Settings:
  seed_raw = os.getenv("GA_SEED", "").strip()
  seed = int(seed_raw) if seed_raw else None

  # /tmp es el único directorio escribible en Cloud Functions
  default_cache = os.getenv(
    "CACHE_DB_PATH",
    "/tmp/cache.sqlite3" if os.getenv("FUNCTION_TARGET") else os.path.join(os.path.dirname(__file__), "cache.sqlite3"),
  )

  return Settings(
    google_maps_api_key=os.getenv("GOOGLE_MAPS_API_KEY", ""),
    firebase_credentials_path=os.getenv("FIREBASE_CREDENTIALS_PATH", ""),
    firebase_project_id=os.getenv("FIREBASE_PROJECT_ID", ""),
    cache_db_path=default_cache,
    ga_population=int(os.getenv("GA_POPULATION", "180")),
    ga_generations=int(os.getenv("GA_GENERATIONS", "320")),
    ga_mutation_rate=float(os.getenv("GA_MUTATION_RATE", "0.15")),
    ga_elite_rate=float(os.getenv("GA_ELITE_RATE", "0.1")),
    ga_tournament_size=int(os.getenv("GA_TOURNAMENT_SIZE", "4")),
    ga_seed=seed,
    default_speed_kmph=float(os.getenv("DEFAULT_SPEED_KMPH", "35")),
    cors_origins=_env_list("CORS_ORIGINS", "http://localhost:5173"),
    allowed_client_ips=_env_list("ALLOWED_CLIENT_IPS"),
  )
