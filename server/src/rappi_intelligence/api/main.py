"""FastAPI application assembly."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from rappi_intelligence.api.routes import chat, dataset, health, providers, report

app = FastAPI(title="Rappi Operations Intelligence API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health.router)
app.include_router(dataset.router)
app.include_router(providers.router)
app.include_router(chat.router)
app.include_router(report.router)
