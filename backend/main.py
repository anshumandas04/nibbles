from contextlib import asynccontextmanager
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import get_settings
from app.core.logging import setup_logging, get_logger
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.middleware.compression import DecompressionMiddleware
from app.services.storage_service import StorageService
from app.services.dashboard_service import set_server_start_time

# Import routers
from app.api import health, backup, upload, media, download, device, cleanup, dashboard

logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Setup logging
    setup_logging()
    settings = get_settings()
    logger.info(f"Starting {settings.APP_NAME} v{settings.BUILD_VERSION} in lifespan context...")
    
    # 2. Ensure directories exist
    storage = StorageService()
    storage.ensure_directories()
    
    # 3. Set start time for uptime tracking
    set_server_start_time()
    
    logger.info("Application initialization complete.")
    yield
    logger.info("Application shutdown initiated.")

def create_app() -> FastAPI:
    settings = get_settings()
    
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.BUILD_VERSION,
        description="Low data-usage cloud sync and backup backend for mobile devices.",
        lifespan=lifespan
    )
    
    # Setup rate limiter
    limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT])
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )
    
    # Add custom middlewares
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(DecompressionMiddleware)
    
    # Ensure static directory exists and mount it
    static_dir = os.path.join(os.path.dirname(__file__), "app", "static")
    os.makedirs(static_dir, exist_ok=True)
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    
    # Include API Routers
    app.include_router(health.router)
    app.include_router(backup.router)
    app.include_router(upload.router)
    app.include_router(media.router)
    app.include_router(download.router)
    app.include_router(device.router)
    app.include_router(cleanup.router)
    app.include_router(dashboard.router)
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception encountered: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Internal Server Error",
                "detail": str(exc) if settings.LOG_LEVEL.upper() == "DEBUG" else "An unexpected error occurred."
            }
        )
        
    return app

app = create_app()
