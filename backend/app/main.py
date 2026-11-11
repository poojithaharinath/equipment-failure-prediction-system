import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.core.database import init_db

# Import API routers
from backend.app.api.plants import router as plants_router
from backend.app.api.production_lines import router as lines_router
from backend.app.api.machines import router as machines_router
from backend.app.api.sensors import router as sensors_router
from backend.app.api.telemetry import router as telemetry_router
from backend.app.api.predictions import router as predictions_router
from backend.app.api.work_orders import router as work_orders_router
from backend.app.api.failure_events import router as failure_events_router
from backend.app.api.technicians import router as technicians_router
from backend.app.api.parts import router as parts_router
from backend.app.api.alerts import router as alerts_router
from backend.app.api.validation import router as validation_router
from backend.app.api.model_evaluation import router as model_eval_router
from backend.app.api.dashboard import router as dashboard_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PredictiveMaintenanceAPI")

app = FastAPI(
    title="AI-Based Predictive Maintenance System API",
    description="End-to-end industrial IoT telemetry monitoring, equipment failure prediction, and maintenance management REST API.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for local dev & docker
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    logger.info("Initializing database schema and checking model availability...")
    init_db()
    logger.info("Application startup completed successfully.")

# Mount API Routers
app.include_router(dashboard_router, prefix=settings.API_V1_PREFIX)
app.include_router(plants_router, prefix=settings.API_V1_PREFIX)
app.include_router(lines_router, prefix=settings.API_V1_PREFIX)
app.include_router(machines_router, prefix=settings.API_V1_PREFIX)
app.include_router(sensors_router, prefix=settings.API_V1_PREFIX)
app.include_router(telemetry_router, prefix=settings.API_V1_PREFIX)
app.include_router(predictions_router, prefix=settings.API_V1_PREFIX)
app.include_router(work_orders_router, prefix=settings.API_V1_PREFIX)
app.include_router(failure_events_router, prefix=settings.API_V1_PREFIX)
app.include_router(technicians_router, prefix=settings.API_V1_PREFIX)
app.include_router(parts_router, prefix=settings.API_V1_PREFIX)
app.include_router(alerts_router, prefix=settings.API_V1_PREFIX)
app.include_router(validation_router, prefix=settings.API_V1_PREFIX)
app.include_router(model_eval_router, prefix=settings.API_V1_PREFIX)

@app.get("/")
def root():
    return {
        "system": "AI-Based Predictive Maintenance System",
        "version": "1.0.0",
        "status": "OPERATIONAL",
        "docs_url": "/docs",
        "api_prefix": settings.API_V1_PREFIX
    }

@app.get("/health")
def health_check():
    return {
        "status": "HEALTHY",
        "database": "CONNECTED",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
