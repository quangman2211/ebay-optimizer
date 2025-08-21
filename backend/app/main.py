from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime

from app.core.config import settings
from app.api.endpoints import listings, optimize, auth, orders, sources, accounts, dashboard, export, sync
from app.db.database import engine
from app.models import database_models

# Create database tables
database_models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    auth.router,
    prefix=f"{settings.API_V1_STR}/auth",
    tags=["authentication"]
)

app.include_router(
    listings.router,
    prefix=f"{settings.API_V1_STR}/listings",
    tags=["listings"]
)

app.include_router(
    optimize.router,
    prefix=f"{settings.API_V1_STR}/optimize",
    tags=["optimization"]
)

app.include_router(
    orders.router,
    prefix=f"{settings.API_V1_STR}/orders",
    tags=["orders"]
)

app.include_router(
    sources.router,
    prefix=f"{settings.API_V1_STR}/sources",
    tags=["sources"]
)

app.include_router(
    accounts.router,
    prefix=f"{settings.API_V1_STR}/accounts",
    tags=["accounts"]
)

app.include_router(
    dashboard.router,
    prefix=f"{settings.API_V1_STR}/dashboard",
    tags=["dashboard"]
)

app.include_router(
    export.router,
    prefix=f"{settings.API_V1_STR}/export",
    tags=["export"]
)

app.include_router(
    sync.router,
    prefix=f"{settings.API_V1_STR}/sync",
    tags=["sync"]
)

@app.get("/")
async def root():
    return {
        "message": "eBay Listing Optimizer API",
        "version": settings.VERSION,
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected error occurred",
            "error": str(exc)
        }
    )