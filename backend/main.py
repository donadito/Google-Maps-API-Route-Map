import asyncio
import os

import functions_framework
import httpx
import firebase_admin
from firebase_admin import auth as fb_auth, credentials
from flask import Request, jsonify, make_response

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
        # En GCP usa las credenciales de la cuenta de servicio del proyecto
        firebase_admin.initialize_app(
            options={"projectId": os.getenv("FIREBASE_PROJECT_ID", "")}
        )
    _firebase_initialized = True


def _check_ip(request: Request, allowed_ips: list[str]) -> bool:
    if not allowed_ips:
        return True
    # X-Forwarded-For contiene la IP real del cliente detrás del load balancer de GCP
    forwarded = request.headers.get("X-Forwarded-For", "")
    client_ip = forwarded.split(",")[0].strip() if forwarded else request.remote_addr
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


@functions_framework.http
def optimize(request: Request):
    settings = get_settings()

    # CORS preflight
    origin = request.headers.get("Origin", "")
    cors_origin = origin if origin in settings.cors_origins else (
        settings.cors_origins[0] if settings.cors_origins else "*"
    )
    if request.method == "OPTIONS":
        resp = make_response("", 204)
        resp.headers["Access-Control-Allow-Origin"] = cors_origin
        resp.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return resp

    # IP whitelist
    if not _check_ip(request, settings.allowed_client_ips):
        return jsonify({"detail": "Forbidden"}), 403

    # Firebase auth
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"detail": "Unauthorized"}), 401

    id_token = auth_header.removeprefix("Bearer ").strip()
    try:
        _init_firebase(settings)
        fb_auth.verify_id_token(id_token)
    except Exception:
        return jsonify({"detail": "Invalid or expired token"}), 401

    if not settings.google_maps_api_key:
        return jsonify({"detail": "Falta GOOGLE_MAPS_API_KEY en las variables de entorno"}), 500

    # Validar y parsear body
    try:
        body = request.get_json(force=True)
        payload = OptimizeRequest.model_validate(body)
    except Exception as exc:
        return jsonify({"detail": str(exc)}), 400

    # Ejecutar optimizacion
    try:
        result = asyncio.run(_run_optimization(payload, settings))
    except Exception as exc:
        return jsonify({"detail": str(exc)}), 502

    resp = jsonify(result)
    resp.headers["Access-Control-Allow-Origin"] = cors_origin
    return resp
