from typing import List, Optional
from .schemas import ProfessorCreate, ProfessorUpdate, ProfessorResponse
from app.auth.auth_service import AuthService
from pydantic import EmailStr
from .repository import ProfessorRepository

class ProfessorService:
    """Serviço para gerenciar professores"""
    def __init__(self, repository: ProfessorRepository, auth_service: AuthService):
        self.repository = repository
        self.auth_service = auth_service
    
    async def _map_to_response(self, professor_model) -> ProfessorResponse:
        """Helper para mapear o modelo Prisma para o schema de resposta."""
        return ProfessorResponse(
            professor_id=professor_model.Professor_ID,
            nome=professor_model.Nome,
            email=professor_model.Email
        )
    
    async def get_all_professores(self) -> List[ProfessorResponse]:
        professores = await self.repository.get_all()
        return [await self._map_to_response(p) for p in professores]
    
    async def get_professor_by_id(self, professor_id: int) -> Optional[ProfessorResponse]:
        professor = await self.repository.get_by_id(professor_id)
        if not professor:
            return None
        return await self._map_to_response(professor)
    
    async def create_professor(self, professor_data:ProfessorCreate) -> ProfessorResponse:
        existing_professor = await self.repository.get_by_email(professor_data.email)
        if existing_professor:
            raise ValueError("Email já está em uso")
        
        hashed_password = self.auth_service._hash_password(professor_data.senha)

        new_professor_data = {
            "Nome": professor_data.nome,
            "Email": professor_data.email,
            "Senha": professor_data.senha
        }

        new_professor_data = await self.repository.create(new_professor_data)
        return await self._map_to_response(new_professor_data)
    
    async def update_professor(self, professor_id: int, professor_data:ProfessorUpdate) -> Optional[ProfessorResponse]:
        existing_professor = await self.repository.get_by_id(professor_id)
        if existing_professor:
            None
        
        update_data = professor_data.model_dump(exclude_unset=True)

        if "email" in update_data and update_data["email"] != existing_professor.Email:
            email_exists = await self.repository.get_by_email(update_data["email"])
            if email_exists:
                raise ValueError("Email já está em uso")
        
        if "senha" in update_data:
            update_data["Senha"] = self.auth_service._hash_password(update_data.pop("senha"))
        
        #Renomeia chaves para corresponder ao Prisma
        if "nome" in update_data: update_data["Nome"] = update_data.pop("nome")
        if "email" in update_data: update_data["Email"] = update_data.pop("email")

        if not update_data: # Se nada foi enviado para atualizar
             return await self._map_to_response(existing_professor)

        updated_professor = await self.repository.update(professor_id, update_data)
        return await self._map_to_response(updated_professor)
    
    async def delete_professor(self, professor_id: int) -> bool:
        deleted = await self.repository.delete(professor_id)
        return await self._map_to_response(deleted)