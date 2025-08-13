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

from .api.v1.endpoints import auth, keys, chat, payments, users, fines, tasks, appointments, admin, documents

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(keys.router, prefix="/api/v1/keys", tags=["API Keys"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["Conversational AI"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["Payments"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(fines.router, prefix="/api/v1/fines", tags=["Fines"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["Admin Tasks"])
app.include_router(appointments.router, prefix="/api/v1", tags=["Appointments"]) # Rooted at /api/v1 to have /procedures and /appointments
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin Data"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documents"])

# We will include other routers here later

# Mount static files for the landing page
app.mount("/static", StaticFiles(directory="frontend_web"), name="static")
# Mount user-uploaded documents for public access
app.mount("/storage", StaticFiles(directory="storage"), name="storage")

@app.get("/")
async def read_index():
    return FileResponse('frontend_web/index.html')
