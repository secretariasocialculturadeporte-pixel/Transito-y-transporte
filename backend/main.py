from fastapi import FastAPI
from .database import engine
from . import models_db

# Create all database tables
models_db.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Tránsito y Movilidad API",
    description="API para la gestión de entidades de tránsito, multas, vehículos y más.",
    version="1.0.0"
)

from .api.v1.endpoints import auth

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Tránsito y Movilidad API"}

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])

# We will include other routers here later
