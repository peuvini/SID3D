from fastapi import Depends
from prisma import Prisma

# Imports para Professor e Auth 
from app.professor.repository import ProfessorRepository
from app.professor.service import ProfessorService
from app.auth.auth_service import AuthService
#Imports DICOM
from app.dicom.repository import DICOMRepository
from app.dicom.service import DICOMService
from app.utils.mesh_generator import MeshGeneratorAbstract # <- Este arquivo precisa ser criado!

# --- Instâncias Globais ---
db = Prisma()
auth_service = AuthService()

# --- Implementação "Dummy" (Temporária) para o MeshGenerator ---
class DummyMeshGenerator(MeshGeneratorAbstract):
    def convert_to_mesh(self, source_file_key: str):
        print(f"SIMULAÇÃO: Geração de malha para o arquivo {source_file_key} seria iniciada aqui.")
        pass

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