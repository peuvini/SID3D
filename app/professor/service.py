from typing import List, Optional
from fastapi import HTTPException
from .schemas import ProfessorCreate, ProfessorUpdate, ProfessorResponse, ProfessorSearch, PasswordChangeRequest
from app.auth.auth_service import AuthService
from .repository import ProfessorRepository

class ProfessorService:
    """Serviço para gerenciar professores"""
    
    def __init__(self, repository: ProfessorRepository, auth_service: AuthService):
        self.repository = repository
        self.auth_service = auth_service
    
    async def _map_to_response(self, professor_model) -> ProfessorResponse:
        """Helper para mapear o modelo Prisma para o schema de resposta."""
        if not professor_model:
            return None
            
        return ProfessorResponse(
            professor_id=professor_model.Professor_ID,
            nome=professor_model.Nome,
            email=professor_model.Email,
            created_at=professor_model.created_at.isoformat() if hasattr(professor_model, 'created_at') and professor_model.created_at else None
        )
    
    async def get_all_professores(self) -> List[ProfessorResponse]:
        """Retorna todos os professores."""
        professores = await self.repository.get_all()
        return [await self._map_to_response(p) for p in professores if p]
    
    async def get_professor_by_id(self, professor_id: int) -> Optional[ProfessorResponse]:
        """Retorna um professor específico pelo ID."""
        professor = await self.repository.get_by_id(professor_id)
        return await self._map_to_response(professor) if professor else None
    
    async def search_professores(self, search_params: ProfessorSearch) -> List[ProfessorResponse]:
        """Busca professores com base nos parâmetros fornecidos."""
        search_criteria = {}
        
        if search_params.nome:
            search_criteria["Nome"] = search_params.nome
        if search_params.email:
            search_criteria["Email"] = search_params.email
            
        professores = await self.repository.search_professors(search_criteria)
        return [await self._map_to_response(p) for p in professores if p]
    
    async def create_professor(self, professor_data: ProfessorCreate) -> ProfessorResponse:
        """Cria um novo professor."""
        # Verificar se email já existe
        if await self.repository.email_exists(professor_data.email):
            raise HTTPException(status_code=400, detail="Email já está em uso")
        
        # Hash da senha
        hashed_password = self.auth_service._hash_password(professor_data.senha)

        # Preparar dados para o banco
        new_professor_data = {
            "Nome": professor_data.nome.strip(),
            "Email": professor_data.email.lower(),
            "Senha": hashed_password
        }

        try:
            new_professor = await self.repository.create(new_professor_data)
            return await self._map_to_response(new_professor)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao criar professor: {str(e)}")
    
    async def update_professor(self, professor_id: int, professor_data: ProfessorUpdate, current_user_id: Optional[int] = None) -> Optional[ProfessorResponse]:
        """Atualiza um professor existente."""
        # Verificar se o professor existe
        existing_professor = await self.repository.get_by_id(professor_id)
        if not existing_professor:
            return None
        
        # Verificar permissão (apenas o próprio professor pode se editar)
        if current_user_id and current_user_id != professor_id:
            raise HTTPException(status_code=403, detail="Você só pode editar seu próprio perfil")
        
        # Preparar dados para atualização
        update_data = {}
        
        if professor_data.nome is not None:
            update_data["Nome"] = professor_data.nome.strip()
        
        if professor_data.email is not None:
            email_lower = professor_data.email.lower()
            # Verificar se o novo email já está em uso (excluindo o próprio professor)
            if await self.repository.email_exists(email_lower, exclude_id=professor_id):
                raise HTTPException(status_code=400, detail="Email já está em uso")
            update_data["Email"] = email_lower
        
        if professor_data.senha is not None:
            update_data["Senha"] = self.auth_service._hash_password(professor_data.senha)

        # Se nada foi enviado para atualizar
        if not update_data:
            return await self._map_to_response(existing_professor)

        try:
            updated_professor = await self.repository.update(professor_id, update_data)
            return await self._map_to_response(updated_professor)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao atualizar professor: {str(e)}")
    
    async def change_password(self, professor_id: int, password_data: PasswordChangeRequest, current_user_id: int) -> bool:
        """Altera a senha de um professor."""
        # Verificar permissão
        if current_user_id != professor_id:
            raise HTTPException(status_code=403, detail="Você só pode alterar sua própria senha")
        
        # Verificar se o professor existe
        professor = await self.repository.get_by_id(professor_id)
        if not professor:
            raise HTTPException(status_code=404, detail="Professor não encontrado")
        
        # Verificar senha atual
        if not self.auth_service._verify_password(password_data.senha_atual, professor.Senha):
            raise HTTPException(status_code=400, detail="Senha atual incorreta")
        
        # Atualizar senha
        hashed_new_password = self.auth_service._hash_password(password_data.nova_senha)
        
        try:
            await self.repository.update(professor_id, {"Senha": hashed_new_password})
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao alterar senha: {str(e)}")
    
    async def delete_professor(self, professor_id: int, current_user_id: int) -> bool:
        """Deleta um professor."""
        # Verificar se o professor existe
        professor = await self.repository.get_by_id(professor_id)
        if not professor:
            return False
        
        # Verificar permissão (apenas o próprio professor pode se deletar)
        if current_user_id != professor_id:
            raise HTTPException(status_code=403, detail="Você só pode deletar seu próprio perfil")
        
        try:
            deleted = await self.repository.delete(professor_id)
            return deleted is not None
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao deletar professor: {str(e)}")
    
    async def get_statistics(self) -> dict:
        """Retorna estatísticas dos professores."""
        try:
            total_professores = await self.repository.count_total()
            return {
                "total_professores": total_professores
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {str(e)}")