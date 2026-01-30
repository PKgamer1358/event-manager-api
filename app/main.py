from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.config import settings
from app.routers import auth, events, registrations, colleges, users, notifications

from fastapi import FastAPI
from app.core.scheduler import start_scheduler
from fastapi.middleware.cors import CORSMiddleware
from app.routers import analytics




start_scheduler()  # ✅ app startup

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="A comprehensive API for managing college events with user authentication and registration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import logging

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    logging.error(f"Validation Error: {exc.errors()}")
    logging.error(f"Request Body: {await request.body()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": str(exc)},
    )




origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://10.0.2.2",
    "http://10.0.2.2:3000",
    "http://10.0.2.2:8000",
    "https://event-manager-ui-two.vercel.app",
    "https://www.event-manager-ui-two.vercel.app"
]


# Add origins from configuration
if settings.ALLOWED_ORIGINS:
    origins.extend(settings.allowed_origins_list)


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"(https?|capacitor|ionic)://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+|.*\.vercel\.app)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static directory for uploads (Removed: Using Cloudinary)
# os.makedirs("uploads", exist_ok=True)
# app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


# Include routers
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(users.router, prefix=settings.API_V1_PREFIX)
app.include_router(events.router, prefix=settings.API_V1_PREFIX)
app.include_router(registrations.router, prefix=settings.API_V1_PREFIX)
app.include_router(notifications.router, prefix="/api") 
app.include_router(analytics.router)
# app.include_router(colleges.router, prefix=settings.API_V1_PREFIX)


@app.get("/")
def root():
    """
    Root endpoint
    """
    return {
        "message": "Event Manager API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
