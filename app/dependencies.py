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
from app.arquivo3D.factory import Arquivo3DAbstractFactory
from app.utils.mesh_generator import MeshGeneratorAbstract # <- Este arquivo precisa ser criado!

# --- Instâncias Globais ---
db = Prisma()
auth_service = AuthService()

# --- Implementação "Dummy" (Temporária) para o MeshGenerator ---
class DummyMeshGenerator(MeshGeneratorAbstract):
    def convert_to_mesh(self, source_file_key: str):
        print(f"SIMULAÇÃO: Geração de malha para o arquivo {source_file_key} seria iniciada aqui.")
        pass

# --- Implementação "Dummy" (Temporária) para o Arquivo3DFactory ---
class DummyArquivo3DFactory(Arquivo3DAbstractFactory):
    def generate(self, dicom_files_content: List[bytes], file_format: str = "stl") -> bytes:
        print(f"SIMULAÇÃO: Geração de arquivo 3D no formato {file_format} a partir de {len(dicom_files_content)} arquivos DICOM.")
        # Retorna dados dummy para teste
        return b"dummy 3d file content"

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
    Cria e injeta as dependências necessárias (repositório e mesh_generator).
    """
    mesh_generator = DummyMeshGenerator()
    return DICOMService(repository=repository, mesh_generator=mesh_generator)

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
    generator = DummyArquivo3DFactory()
    return Arquivo3DService(
        repository=repository,
        dicom_repository=dicom_repository,
        generator=generator
    )