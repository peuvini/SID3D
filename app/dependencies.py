from fastapi import Depends
from prisma import Prisma
from typing import List

# Imports para Professor e Auth 
from app.professor.repository import ProfessorRepository
from app.professor.service import ProfessorService
from app.auth.auth_service import AuthService
#Imports DICOM
from app.dicom.repository import DICOMRepository
from app.dicom.service import DICOMService
# Imports Arquivo3D
from app.arquivo3D.repository import Arquivo3DRepository
from app.arquivo3D.service import Arquivo3DService
from app.arquivo3D.factory import Arquivo3DAbstractFactory, Arquivo3DFactoryImpl, Arquivo3DFactoryDummy

# --- Instâncias Globais ---
db = Prisma()
auth_service = AuthService()

# --- Factory para geração de arquivos 3D ---
try:
    # Tenta usar a implementação real
    arquivo3d_factory = Arquivo3DFactoryImpl(iso_value=100.0, smooth=True)
    print("✅ Usando Arquivo3DFactoryImpl (implementação real)")
except ImportError as e:
    # Fallback para implementação dummy se bibliotecas não estiverem disponíveis
    arquivo3d_factory = Arquivo3DFactoryDummy()
    print(f"⚠️ Usando Arquivo3DFactoryDummy - Bibliotecas não disponíveis: {e}")

# --- Provedores de Dependência (Providers) ---
def get_db() -> Prisma:
    return db

def get_auth_service() -> AuthService:
    return auth_service

# --- Dependências do Professor ---
def get_professor_repository(db: Prisma = Depends(get_db)) -> ProfessorRepository:
    return ProfessorRepository(db)

def get_professor_service(
        repository: ProfessorRepository = Depends(get_professor_repository),
        auth_service: AuthService = Depends(get_auth_service)
) -> ProfessorService:
    return ProfessorService(repository, auth_service)

# --- DICOM ---
def get_dicom_repository(db: Prisma = Depends(get_db)) -> DICOMRepository:
    """Provedor para o repositório DICOM."""
    return DICOMRepository(db)

def get_dicom_service(
    repository: DICOMRepository = Depends(get_dicom_repository)
) -> DICOMService:
    """
    Provedor para o serviço DICOM.
    Cria e injeta as dependências necessárias (repositório).
    """
    return DICOMService(repository=repository)

# --- Arquivo3D ---
def get_arquivo3d_repository(db: Prisma = Depends(get_db)) -> Arquivo3DRepository:
    """Provedor para o repositório Arquivo3D."""
    return Arquivo3DRepository(db)

def get_arquivo3d_service(
    repository: Arquivo3DRepository = Depends(get_arquivo3d_repository),
    dicom_repository: DICOMRepository = Depends(get_dicom_repository)
) -> Arquivo3DService:
    """
    Provedor para o serviço Arquivo3D.
    Cria e injeta as dependências necessárias (repositório, dicom_repository e generator).
    """
    return Arquivo3DService(
        repository=repository,
        dicom_repository=dicom_repository,
        generator=arquivo3d_factory
    )