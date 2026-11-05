from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.v1 import api_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.db.session import engine
from app.middleware.correlation import CorrelationIdMiddleware
from app.middleware.rate_limit import AuthRateLimitMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware

configure_logging()
settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Secure healthcare management API (academic / synthetic data only).",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(AuthRateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)

register_exception_handlers(app)
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name, "env": settings.app_env}


@app.get("/ready")
def ready() -> dict[str, str]:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ready", "database": "ok"}
    except Exception:
        from fastapi import HTTPException

        raise HTTPException(status_code=503, detail="Database not ready") from None


@app.get("/metrics")
def metrics() -> dict[str, object]:
    """Minimal metrics placeholder compatible with future Prometheus exporters."""
    return {
        "app": settings.app_name,
        "env": settings.app_env,
        "uptime_hint": "instrument with prometheus_client in later phases",
    }
