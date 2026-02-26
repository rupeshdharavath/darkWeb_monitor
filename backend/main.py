"""
DarkWeb Monitor - FastAPI Main Entry Point
Backend API server using FastAPI
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes import (
    health_router,
    scan_router,
    monitors_router,
    alerts_router,
    history_router,
)


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application
    
    Returns:
        FastAPI: Configured FastAPI application
    """
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Dark Web Monitoring and Threat Intelligence Platform",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_credentials,
        allow_methods=settings.cors_methods,
        allow_headers=settings.cors_headers,
    )

    # Include routers
    app.include_router(health_router, prefix=settings.api_prefix, tags=["Health"])
    app.include_router(scan_router, prefix=settings.api_prefix, tags=["Scan"])
    app.include_router(history_router, prefix=settings.api_prefix, tags=["History"])
    app.include_router(monitors_router, prefix=settings.api_prefix, tags=["Monitors"])
    app.include_router(alerts_router, prefix=settings.api_prefix, tags=["Alerts"])

    return app


# Create the FastAPI application instance
app = create_app()


@app.on_event("startup")
async def startup_event():
    """
    Execute on application startup
    """
    print("=" * 60)
    print("🚀 DarkWeb Monitor API Starting")
    print(f"📋 Version: {settings.app_version}")
    print(f"🌐 Server: http://{settings.host}:{settings.port}")
    print(f"📖 Docs: http://{settings.host}:{settings.port}/docs")
    print("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """
    Execute on application shutdown
    """
    print("=" * 60)
    print("🛑 DarkWeb Monitor API Shutting Down")
    print("=" * 60)


if __name__ == "__main__":
    # Run the application with uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level="info",
    )
