"""
FastAPI application entry point.

- CORS middleware for frontend access
- Lifespan handler for model preloading
- Health check endpoint
- Static file serving
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGINS, DEVICE, SEAMFORMER_WEIGHTS, YOLO_WEIGHTS
from app.models.schemas import HealthResponse
from app.routers.transliterate import router as transliterate_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-30s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# Track model load status
_models_loaded = {"seamformer": False, "yolo": False}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Models are loaded lazily on first request to save startup memory,
    but we log readiness here.
    """
    logger.info("=" * 60)
    logger.info("  DeepLontar — Balinese Lontar Transliteration API")
    logger.info("=" * 60)
    logger.info("  Device      : %s", DEVICE)
    logger.info("  SeamFormer  : %s", SEAMFORMER_WEIGHTS)
    logger.info("  YOLO        : %s", YOLO_WEIGHTS)
    logger.info("  CORS origins: %s", CORS_ORIGINS)
    logger.info("=" * 60)
    logger.info("Models will be loaded on first request (lazy loading)")
    yield
    logger.info("Shutting down...")


# ── Create App ────────────────────────────────────────────
app = FastAPI(
    title="DeepLontar API",
    description="End-to-end Balinese lontar manuscript transliteration system",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────
app.include_router(transliterate_router)


# ── Health Check ──────────────────────────────────────────
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check API and model status."""
    from app.services.segmentation import SeamFormerService
    from app.services.detection import YOLODetectionService

    return HealthResponse(
        status="ok",
        seamformer_loaded=SeamFormerService._instance is not None,
        yolo_loaded=YOLODetectionService._instance is not None,
        device=DEVICE,
    )


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "DeepLontar API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
