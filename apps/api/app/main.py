"""ScamShield AI — FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import CORS_ORIGINS, ENGINE_VERSION
from .database import Base, engine
from .routers import cases, dashboard, graph_reports_audit

app = FastAPI(
    title="ScamShield AI API",
    description=(
        "Digital Arrest Scam Defence & Fraud Intelligence platform (hackathon prototype). "
        "Detect coercion. Interrupt fraud. Protect before payment."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cases.router)
app.include_router(dashboard.router)
app.include_router(graph_reports_audit.router)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


@app.get("/api/health")
def health():
    return {"status": "ok", "engine_version": ENGINE_VERSION}
