from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime

from app.core.config import settings
from app.api.endpoints import listings, optimize, auth, orders, sources, accounts, dashboard, export, sync, drafts, messages, account_sheets, products, roles, sheets_sync
from app.api.endpoints import settings as settings_router
# Temporarily comment out problematic imports for testing
# from app.api.v1 import suppliers, pricing, backup, automation, intelligent_pricing, supplier_analytics, inventory_management, dashboard_analytics
from app.api.v1.products import router as products_v1_router
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

app.include_router(
    settings_router.router,
    prefix=f"{settings.API_V1_STR}/settings",
    tags=["settings"]
)

app.include_router(
    drafts.router,
    prefix=f"{settings.API_V1_STR}/drafts",
    tags=["drafts"]
)

app.include_router(
    messages.router,
    prefix=f"{settings.API_V1_STR}/messages",
    tags=["messages"]
)

app.include_router(
    account_sheets.router,
    prefix=f"{settings.API_V1_STR}/account-sheets",
    tags=["account-sheets"]
)

app.include_router(
    products.router,
    prefix=f"{settings.API_V1_STR}/products",
    tags=["products"]
)

# Enhanced V1 API Endpoints with SOLID Architecture
# Temporarily commented out for testing
# app.include_router(
#     suppliers.router,
#     prefix=f"{settings.API_V1_STR}",
#     tags=["suppliers"]
# )

app.include_router(
    products_v1_router,
    prefix=f"{settings.API_V1_STR}/products-v1",
    tags=["products-enhanced"]
)

# app.include_router(
#     pricing.router,
#     prefix=f"{settings.API_V1_STR}",
#     tags=["pricing"]
# )

app.include_router(
    roles.router,
    prefix=f"{settings.API_V1_STR}/roles",
    tags=["multi-role"]
)

app.include_router(
    sheets_sync.router,
    prefix=f"{settings.API_V1_STR}/sheets",
    tags=["google-sheets"]
)

# app.include_router(
#     backup.router,
#     prefix=f"{settings.API_V1_STR}/backup",
#     tags=["backup-system"]
# )

# app.include_router(
#     automation.router,
#     prefix=f"{settings.API_V1_STR}/automation",
#     tags=["automation-system"]
# )

# app.include_router(
#     intelligent_pricing.router,
#     prefix=f"{settings.API_V1_STR}/intelligent-pricing",
#     tags=["intelligent-pricing"]
# )

# app.include_router(
#     supplier_analytics.router,
#     prefix=f"{settings.API_V1_STR}/supplier-analytics",
#     tags=["supplier-analytics"]
# )

# app.include_router(
#     inventory_management.router,
#     prefix=f"{settings.API_V1_STR}/inventory-management",
#     tags=["inventory-management"]
# )

# app.include_router(
#     dashboard_analytics.router,
#     prefix=f"{settings.API_V1_STR}/dashboard-analytics",
#     tags=["dashboard-analytics"]
# )

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