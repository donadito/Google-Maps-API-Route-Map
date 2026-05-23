from __future__ import annotations

from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .middleware.auth import AuthMiddleware
from .models import OptimizeRequest, OptimizeResponse
from .optimizer.optimizer import GAConfig, optimize_route
from .services.cache import DistanceCache
from .services.distance_matrix import build_distance_matrices, estimate_duration_matrix
from .services.google_api import fetch_directions_polyline
from .utils import compute_totals

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.cache = DistanceCache(settings.cache_db_path)
    app.state.http_client = httpx.AsyncClient(timeout=20.0)
    yield
    await app.state.http_client.aclose()
    app.state.cache.close()


app = FastAPI(title="Route Optimizer API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(AuthMiddleware)


@app.get("/")
def read_root():
    return {"status": "ok"}


@app.post("/optimize", response_model=OptimizeResponse, response_model_by_alias=True)
async def optimize_route_handler(request: Request, payload: OptimizeRequest):
    cache: DistanceCache = request.app.state.cache
    http_client: httpx.AsyncClient = request.app.state.http_client

    places = payload.places
    if any(place.location is None for place in places):
        raise HTTPException(
            status_code=400,
            detail="Cada lugar necesita coordenadas. Usa el autocompletado.",
        )

    if not settings.google_maps_api_key:
        raise HTTPException(
            status_code=400,
            detail="Falta GOOGLE_MAPS_API_KEY en el archivo .env.",
        )

    if payload.weight_matrix is not None:
        distance_matrix = payload.weight_matrix
        if payload.duration_matrix is not None:
            duration_matrix = payload.duration_matrix
        else:
            duration_matrix = estimate_duration_matrix(
                distance_matrix,
                settings.default_speed_kmph,
            )
    else:
        try:
            distance_matrix, duration_matrix = await build_distance_matrices(
                places,
                settings.google_maps_api_key,
                cache,
                http_client,
            )
        except Exception as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    ga_config = GAConfig(
        population_size=settings.ga_population,
        generations=settings.ga_generations,
        mutation_rate=settings.ga_mutation_rate,
        elite_rate=settings.ga_elite_rate,
        tournament_size=settings.ga_tournament_size,
        seed=settings.ga_seed,
    )

    order_indices = optimize_route(
        distance_matrix,
        payload.return_to_origin,
        ga_config,
    )

    total_distance, total_duration = compute_totals(
        order_indices,
        distance_matrix,
        duration_matrix,
        payload.return_to_origin,
    )

    order_ids = [places[index].id for index in order_indices]

    try:
        polyline = await fetch_directions_polyline(
            settings.google_maps_api_key,
            places,
            order_indices,
            payload.return_to_origin,
            http_client,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return OptimizeResponse(
        order=order_ids,
        totalDistanceMeters=int(round(total_distance)),
        totalDurationSeconds=int(round(total_duration)),
        polyline=polyline,
    )
