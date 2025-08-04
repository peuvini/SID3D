from typing import List, Optional
from prisma import Prisma
from prisma.models import Professor as ProfessorModel # Importe o modelo gerado pelo Prisma
from .schemas import ProfessorCreate, ProfessorUpdate

class ProfessorRepository:
    def __init__(self, db: Prisma):
        self.db = db

    async def get_all(self) -> List[ProfessorModel]:
        return await self.db.professor.find_many()
    
    async def get_by_id(self, professor_id:int) -> Optional[ProfessorModel]:
        return await self.db.professor.find_unique(where={"Professor_ID": professor_id})
    
    async def get_by_email(self, email:str) -> Optional[ProfessorModel]:
        return await self.db.professor.find_unique(where={"Email": email})
    
    async def create(self, professor_data:dict) -> ProfessorModel:
        return await self.db.professor.create(data=professor_data)
    
    async def update(self, professor_id:int, update_data:dict) -> Optional[ProfessorModel]:
        return await self.db.professor.update(
            where = {"Professor_ID": professor_id},
            data = update_data
        )
    
    async def delete(self, professor_id:int) -> Optional[ProfessorModel]:
        return await self.db.professor.delete(where={"Professor_ID": professor_id})