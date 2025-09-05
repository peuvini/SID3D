from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import sys
import traceback

# Configurar logging detalhado
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('debug.log')
    ]
)

logger = logging.getLogger(__name__)

# Configurar exceções não tratadas
def custom_excepthook(exctype, value, traceback_obj):
    logger.error("❌ EXCEÇÃO NÃO TRATADA:")
    logger.error(f"Tipo: {exctype}")
    logger.error(f"Valor: {value}")
    logger.error("📋 Stack trace completo:")
    traceback.print_exception(exctype, value, traceback_obj)

sys.excepthook = custom_excepthook

from .dependencies import db
from config import settings

# ---  ROUTERS  ---
from app.auth.auth_controller import router as auth_router
from app.professor.controller import router as professor_router
from app.dicom.controller import router as dicom_router
from app.arquivo3D.controller import router as arquivo3d_router

# --- Gerenciador de Ciclo de Vida (Lifespan) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia os eventos de inicialização e desligamento,
    como a conexão com o banco de dados.
    """
    print("INFO:     Conectando ao banco de dados...")
    await db.connect()
    
    yield  
    
    print("INFO:     Desconectando do banco de dados...")
    await db.disconnect()

# --- Instância Principal do App ---
app = FastAPI(
    title="SID3D API",
    description="Sistema de Impressão 3D - API",
    version="1.0.0",
    debug=True,
    lifespan=lifespan,
    redirect_slashes=False
)

# --- Configuração do CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Inclusão de Rotas ---
app.include_router(auth_router)
app.include_router(professor_router)
app.include_router(dicom_router)
app.include_router(arquivo3d_router)

# --- Endpoints da Raiz ---
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