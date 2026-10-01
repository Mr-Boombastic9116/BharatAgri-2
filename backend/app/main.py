import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.app.core.config import settings
from backend.app.core.database import check_db_connection

# Import all routers
from backend.app.api.health import router as health_router
from backend.app.api.auth import router as auth_router
from backend.app.api.farmers import router as farmers_router
from backend.app.api.agents import router as agents_router
from backend.app.api.centres import router as centres_router
from backend.app.api.slots import router as slots_router
from backend.app.api.bookings import router as bookings_router
from backend.app.api.qr import router as qr_router
from backend.app.api.procurement import router as procurement_router
from backend.app.api.trucks import router as trucks_router
from backend.app.api.inventory import router as inventory_router, bardan_router
from backend.app.api.complaints import router as complaints_router
from backend.app.api.audit import router as audit_router
from backend.app.api.ai import router as ai_router
from backend.app.api.government import router as government_router
from backend.app.api.stats import router as stats_router
from backend.app.api.price import router as price_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bharatagri")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="BharatAgri Iteration 2 - Agricultural Procurement & Intelligence Platform"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Error handling: Uniform structured JSON
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail
    if isinstance(detail, dict):
        code = detail.get("code", "HTTP_ERROR")
        message = detail.get("message", "An error occurred")
    else:
        code = "HTTP_ERROR"
        message = str(detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": {"code": code, "message": message}}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_details = []
    for err in exc.errors():
        field = " -> ".join([str(loc) for loc in err.get("loc", [])])
        msg = err.get("msg", "Invalid value")
        error_details.append(f"{field}: {msg}")
    
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "; ".join(error_details) if error_details else "Invalid request data."
            }
        }
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An internal server error occurred. Please try again later."
            }
        }
    )

# Include Routers with /api prefix for API consistency
app.include_router(health_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(farmers_router, prefix="/api")
app.include_router(agents_router, prefix="/api")
app.include_router(centres_router, prefix="/api")
app.include_router(slots_router, prefix="/api")
app.include_router(bookings_router, prefix="/api")
app.include_router(qr_router, prefix="/api")
app.include_router(procurement_router, prefix="/api")

# Direct root fallbacks for backwards compatibility
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(farmers_router)
app.include_router(agents_router)
app.include_router(centres_router)
app.include_router(slots_router)
app.include_router(bookings_router)
app.include_router(qr_router)
app.include_router(procurement_router)

# Routers that already include /api in their prefix
app.include_router(trucks_router)
app.include_router(inventory_router)
app.include_router(bardan_router)
app.include_router(complaints_router)
app.include_router(audit_router)
app.include_router(ai_router)
app.include_router(government_router)
app.include_router(stats_router)
app.include_router(price_router, prefix="/api")
app.include_router(price_router)

# Mount uploads directory for photo evidence
import os
from fastapi.staticfiles import StaticFiles
uploads_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads"))
os.makedirs(os.path.join(uploads_dir, "evidence"), exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")



@app.on_event("startup")
def startup_event():
    db_ok = check_db_connection()
    if db_ok:
        logger.info("[Startup] Connected to MySQL database successfully.")
    else:
        logger.warning("[Startup] MySQL database connection failed.")
