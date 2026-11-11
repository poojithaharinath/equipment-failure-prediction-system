import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.app.core.config import settings
from backend.app.core.database import check_database
from backend.app.ml.predictor import ModelNotAvailableError, get_model_status

# Import API routers for each endpoint
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
    title=f"{settings.APP_NAME} API",
    description="End-to-end industrial IoT telemetry monitoring, equipment failure prediction, and maintenance management REST API.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ModelNotAvailableError)
def model_not_available_handler(request: Request, exc: ModelNotAvailableError):
    return JSONResponse(status_code=503, content={"detail": str(exc), "error": "MODEL_NOT_AVAILABLE"})


@app.on_event("startup")
def on_startup():
    database = check_database()
    if database["status"] != "CONNECTED":
        logger.error("Database unavailable: %s", database.get("error"))
    model = get_model_status()
    if model["status"] != "LOADED":
        logger.error("ML model unavailable: %s", model["error"])
    logger.info("Application startup completed.")

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
    database = check_database()
    model = get_model_status()
    healthy = database["status"] == "CONNECTED" and model["status"] == "LOADED"
    body = {
        "status": "HEALTHY" if healthy else "UNHEALTHY",
        "database": database,
        "model": model,
        "version": "1.0.0",
    }
    return JSONResponse(status_code=200 if healthy else 503, content=body)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
