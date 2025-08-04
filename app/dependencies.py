from prisma import Prisma
from app.professor.repository import ProfessorRepository
from app.professor.service import ProfessorService
from app.auth.auth_service import AuthService
from fastapi import Depends


db = Prisma()
auth_service = AuthService()

async def get_db():
    return db

def get_auth_service():
    return auth_service

def get_professor_repository(db: Prisma = Depends(get_db)) -> ProfessorRepository:

    return ProfessorRepository(db)

def get_professor_service(
        repository: ProfessorRepository = Depends(get_professor_repository),
        auth_service: AuthService = Depends(get_auth_service)
) -> ProfessorService:
    return ProfessorService(repository, auth_service)