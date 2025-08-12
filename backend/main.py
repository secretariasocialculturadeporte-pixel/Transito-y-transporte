from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .database import engine
from . import models_db

# Create all database tables
models_db.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Tránsito y Movilidad API",
    description="API para la gestión de entidades de tránsito, multas, vehículos y más.",
    version="1.0.0"
)

from .api.v1.endpoints import auth, keys, chat, payments

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(keys.router, prefix="/api/v1/keys", tags=["API Keys"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["Conversational AI"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["Payments"])

# We will include other routers here later

# Mount static files for the landing page
app.mount("/static", StaticFiles(directory="frontend_web"), name="static")

@app.get("/")
async def read_index():
    return FileResponse('frontend_web/index.html')
