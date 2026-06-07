from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import get_settings
from app.routers import dashboard, city, locality, developer, project, rental, demo

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting Datra Analytics API...")
    yield
    # Shutdown
    print("👋 Shutting down Datra Analytics API...")


app = FastAPI(
    title="Datra Analytics API",
    description="Real Estate Analytics Platform - API for fetching and analyzing property data",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(dashboard.router)
app.include_router(city.router)
app.include_router(locality.router)
app.include_router(developer.router)
app.include_router(project.router)
app.include_router(rental.router)
app.include_router(demo.router)


@app.get("/")
async def root():
    return {
        "name": "Datra Analytics API",
        "version": "1.0.0",
        "description": "Real Estate Analytics Platform",
        "docs": "/api/docs"
    }


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "datra-analytics-api"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )
