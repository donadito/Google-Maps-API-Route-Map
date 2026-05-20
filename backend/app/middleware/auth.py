import firebase_admin
from firebase_admin import auth, credentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import get_settings

_firebase_initialized = False


def _init_firebase() -> None:
    global _firebase_initialized
    if _firebase_initialized:
        return
    settings = get_settings()
    cred = credentials.Certificate(settings.firebase_credentials_path)
    firebase_admin.initialize_app(cred)
    _firebase_initialized = True


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        settings = get_settings()

        # IP whitelist — si la lista está vacía se permite todo (modo dev)
        allowed_ips = settings.allowed_client_ips
        if allowed_ips and request.client.host not in allowed_ips:
            return JSONResponse({"detail": "Forbidden"}, status_code=403)

        # Verificación del Firebase ID Token
        authorization = request.headers.get("Authorization", "")
        if not authorization.startswith("Bearer "):
            return JSONResponse({"detail": "Unauthorized"}, status_code=401)

        id_token = authorization.removeprefix("Bearer ").strip()
        try:
            _init_firebase()
            decoded_token = auth.verify_id_token(id_token)
            request.state.uid = decoded_token["uid"]
        except Exception:
            return JSONResponse({"detail": "Invalid or expired token"}, status_code=401)

        return await call_next(request)
