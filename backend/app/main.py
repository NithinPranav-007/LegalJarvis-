"""FastAPI application entrypoint for LegalJarvis."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.qa import router as qa_router
from app.api.search import router as search_router
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    description="Citation-Verified Legal Research and Q&A for Indian Law",
    version="0.1.0",
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth_router)
app.include_router(search_router)
app.include_router(qa_router)


@app.get("/health", tags=["System"])
async def health_check() -> dict[str, str]:
    """Liveness check endpoint."""
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "env": settings.APP_ENV,
        "disclaimer": settings.LEGAL_DISCLAIMER,
    }
