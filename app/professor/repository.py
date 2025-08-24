from typing import List, Optional
from prisma import Prisma
from prisma.models import Professor as ProfessorModel

class ProfessorRepository:
    def __init__(self, db: Prisma):
        self.db = db

    async def get_all(self) -> List[ProfessorModel]:
        """Retorna todos os professores."""
        return await self.db.professor.find_many()
    
    async def get_by_id(self, professor_id: int) -> Optional[ProfessorModel]:
        """Retorna um professor específico pelo ID."""
        return await self.db.professor.find_unique(where={"Professor_ID": professor_id})
    
    async def get_by_email(self, email: str) -> Optional[ProfessorModel]:
        """Retorna um professor específico pelo email."""
        return await self.db.professor.find_unique(where={"Email": email})
    
    async def search_professors(self, search_criteria: dict) -> List[ProfessorModel]:
        """Busca professores com base nos critérios fornecidos."""
        where_clause = {}
        
        # Busca case-insensitive por nome
        if search_criteria.get('Nome'):
            where_clause['Nome'] = {
                'contains': search_criteria['Nome'],
                'mode': 'insensitive'
            }
        
        # Busca case-insensitive por email
        if search_criteria.get('Email'):
            where_clause['Email'] = {
                'contains': search_criteria['Email'],
                'mode': 'insensitive'
            }
        
        return await self.db.professor.find_many(
            where=where_clause
        )
    
    async def create(self, professor_data: dict) -> ProfessorModel:
        """Cria um novo professor."""
        return await self.db.professor.create(data=professor_data)
    
    async def update(self, professor_id: int, update_data: dict) -> Optional[ProfessorModel]:
        """Atualiza um professor existente."""
        return await self.db.professor.update(
            where={"Professor_ID": professor_id},
            data=update_data
        )
    
    async def delete(self, professor_id: int) -> Optional[ProfessorModel]:
        """Deleta um professor."""
        return await self.db.professor.delete(where={"Professor_ID": professor_id})
    
    async def count_total(self) -> int:
        """Conta o total de professores cadastrados."""
        return await self.db.professor.count()
    
    async def email_exists(self, email: str, exclude_id: Optional[int] = None) -> bool:
        """Verifica se um email já está em uso (excluindo um ID específico)."""
        where_clause = {"Email": email}
        if exclude_id:
            where_clause["Professor_ID"] = {"not": exclude_id}
        
        professor = await self.db.professor.find_first(where=where_clause)
        return professor is not None