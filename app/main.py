"""FastAPI application for Gabrr Budget transaction parsing."""

from fastapi import FastAPI

from app.api import router as api_router

app = FastAPI(
    title="Gabrr Budget API",
    description="Parse financial documents (CSV/PDF) into normalized transactions",
    version="0.1.0",
)

app.include_router(api_router)
