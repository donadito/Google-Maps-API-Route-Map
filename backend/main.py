import asyncio
import os

import firebase_admin
from firebase_admin import auth as fb_auth, credentials
from firebase_functions import https_fn, options
from flask import jsonify, make_response
import httpx

from app.config import get_settings
from app.models import OptimizeRequest
from app.optimizer.optimizer import GAConfig, optimize_route
from app.services.cache import DistanceCache
from app.services.distance_matrix import build_distance_matrices, estimate_duration_matrix
from app.services.google_api import fetch_directions_polyline
from app.utils import compute_totals

_firebase_initialized = False


def _init_firebase(settings) -> None:
    global _firebase_initialized
    if _firebase_initialized:
        return
    cred_path = settings.firebase_credentials_path
    if cred_path and os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    else:
        firebase_admin.initialize_app(
            options={"projectId": settings.firebase_project_id or os.getenv("GCLOUD_PROJECT", "")}
        )
    _firebase_initialized = True


def _check_ip(req: https_fn.Request, allowed_ips: list[str]) -> bool:
    if not allowed_ips:
        return True
    forwarded = req.headers.get("X-Forwarded-For", "")
    client_ip = forwarded.split(",")[0].strip() if forwarded else req.remote_addr
    return client_ip in allowed_ips


async def _run_optimization(payload: OptimizeRequest, settings) -> dict:
    cache = DistanceCache(settings.cache_db_path)
    try:
        async with httpx.AsyncClient(timeout=30.0) as http_client:
            if payload.weight_matrix is not None:
                distance_matrix = payload.weight_matrix
                duration_matrix = (
                    payload.duration_matrix
                    if payload.duration_matrix is not None
                    else estimate_duration_matrix(distance_matrix, settings.default_speed_kmph)
                )
            else:
                distance_matrix, duration_matrix = await build_distance_matrices(
                    payload.places,
                    settings.google_maps_api_key,
                    cache,
                    http_client,
                )

            ga_config = GAConfig(
                population_size=settings.ga_population,
                generations=settings.ga_generations,
                mutation_rate=settings.ga_mutation_rate,
                elite_rate=settings.ga_elite_rate,
                tournament_size=settings.ga_tournament_size,
                seed=settings.ga_seed,
            )

            order_indices = optimize_route(distance_matrix, payload.return_to_origin, ga_config)
            total_distance, total_duration = compute_totals(
                order_indices, distance_matrix, duration_matrix, payload.return_to_origin
            )
            order_ids = [payload.places[i].id for i in order_indices]
            polyline = await fetch_directions_polyline(
                settings.google_maps_api_key,
                payload.places,
                order_indices,
                payload.return_to_origin,
                http_client,
            )
    finally:
        cache.close()

    return {
        "order": order_ids,
        "totalDistanceMeters": int(round(total_distance)),
        "totalDurationSeconds": int(round(total_duration)),
        "polyline": [{"lat": p.lat, "lng": p.lng} for p in polyline],
    }


@https_fn.on_request(
    region="us-central1",
    memory=options.MemoryOption.MB_512,
    timeout_sec=120,
    cors=options.CorsOptions(
        cors_origins="*",
        cors_methods=["GET", "POST", "OPTIONS"],
    ),
)
def optimize(req: https_fn.Request) -> https_fn.Response:
    settings = get_settings()

    # IP whitelist
    if not _check_ip(req, settings.allowed_client_ips):
        return https_fn.Response(response='{"detail":"Forbidden"}', status=403, mimetype="application/json")

    # Firebase auth
    auth_header = req.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return https_fn.Response(response='{"detail":"Unauthorized"}', status=401, mimetype="application/json")

    id_token = auth_header.removeprefix("Bearer ").strip()
    try:
        _init_firebase(settings)
        fb_auth.verify_id_token(id_token)
    except Exception:
        return https_fn.Response(response='{"detail":"Invalid or expired token"}', status=401, mimetype="application/json")

    if not settings.google_maps_api_key:
        return https_fn.Response(response='{"detail":"Falta GOOGLE_MAPS_API_KEY"}', status=500, mimetype="application/json")

    try:
        body = req.get_json(force=True)
        payload = OptimizeRequest.model_validate(body)
    except Exception as exc:
        import json
        return https_fn.Response(response=json.dumps({"detail": str(exc)}), status=400, mimetype="application/json")

    try:
        result = asyncio.run(_run_optimization(payload, settings))
    except Exception as exc:
        import json
        return https_fn.Response(response=json.dumps({"detail": str(exc)}), status=502, mimetype="application/json")

    import json
    return https_fn.Response(response=json.dumps(result), status=200, mimetype="application/json")
