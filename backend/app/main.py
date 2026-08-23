from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.responses import JSONResponse
from .config import settings
from .database import init_db
from .health import configuration_status, readiness_status
from .security import RequestSecurityMiddleware
from .routers import sellers, products, orders, intelligence, weather, media, financial, risk, actions, integrations, auth

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="GramSell AI API", version="1.2.0", lifespan=lifespan)
app.add_middleware(RequestSecurityMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1024)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Content-Type", "Authorization", "X-GramSell-API-Key", "X-Request-ID"],
)

@app.exception_handler(Exception)
async def unhandled_exception(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "request_id": getattr(request.state, "request_id", None)},
    )

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(sellers.router, prefix="/api/sellers", tags=["sellers"])
app.include_router(products.router, prefix="/api/products", tags=["products"])
app.include_router(orders.router, prefix="/api/orders", tags=["orders"])
app.include_router(intelligence.router, prefix="/api/intelligence", tags=["intelligence"])
app.include_router(weather.router, prefix="/api/weather", tags=["weather"] )
app.include_router(media.router, prefix="/api/media", tags=["media"])
app.include_router(financial.router, prefix="/api/financial", tags=["financial"])
app.include_router(risk.router, prefix="/api/risk", tags=["risk"])
app.include_router(actions.router, prefix="/api/actions", tags=["actions"])
app.include_router(integrations.router, prefix="/api/integrations", tags=["integrations"])

@app.get("/health")
def health():
    return {"status": "ok", "configuration": configuration_status()}

@app.get("/ready")
def ready():
    result = readiness_status()
    return JSONResponse(status_code=200 if result["ready"] else 503, content=result)
