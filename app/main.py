from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .dependencies import db
from config import settings

# ---  ROUTERS  ---
from app.auth.auth_controller import router as auth_router
from app.professor.controller import router as professor_router
from app.dicom.controller import router as dicom_router 

app = FastAPI(
    title="SID3D API",
    description="Sistema de Impressão 3D - API",
    version="1.0.0"
)

# Configuração do CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    await db.connect()

@app.on_event("shutdown")
async def shutdown():
    await db.disconnect()

# --- 2. INCLUA OS ROUTERS NA APLICAÇÃO ---
app.include_router(auth_router)
app.include_router(professor_router)
app.include_router(dicom_router)

@app.get("/")
async def root():
    """Endpoint raiz da API"""
    return {
        "message": "Bem-vindo à API do SID3D",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Endpoint para verificar a saúde da API"""
    return {"status": "healthy"}