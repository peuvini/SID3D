from typing import List, Optional
from prisma import Prisma
from .schemas import ProfessorCreate, ProfessorUpdate, ProfessorResponse
from app.auth.auth_service import AuthService


class ProfessorService:
    """Serviço para gerenciar professores"""
    
    def __init__(self):
        self.prisma = Prisma()
    
    async def __aenter__(self):
        await self.prisma.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.prisma.disconnect()
    
    async def get_all_professores(self) -> List[ProfessorResponse]:
        """Retorna todos os professores"""
        professors = await self.prisma.professor.find_many()
        return [
            ProfessorResponse(
                professor_id=prof.Professor_ID,
                nome=prof.Nome,
                email=prof.Email
            )
            for prof in professors
        ]
    
    async def get_professor_by_id(self, professor_id: int) -> Optional[ProfessorResponse]:
        """Retorna um professor específico por ID"""
        professor = await self.prisma.professor.find_unique(
            where={"Professor_ID": professor_id}
        )
        
        if not professor:
            return None
        
        return ProfessorResponse(
            professor_id=professor.Professor_ID,
            nome=professor.Nome,
            email=professor.Email
        )
    
    async def create_professor(self, professor_data: ProfessorCreate) -> ProfessorResponse:
        """Cria um novo professor"""
        # Verifica se o email já existe
        existing_professor = await self.prisma.professor.find_unique(
            where={"Email": professor_data.email}
        )
        
        if existing_professor:
            raise ValueError("Email já está em uso")
        
        # Hash da senha
        auth_service = AuthService()
        hashed_password = auth_service._hash_password(professor_data.senha)
        
        # Cria o professor
        new_professor = await self.prisma.professor.create(
            data={
                "Nome": professor_data.nome,
                "Email": professor_data.email,
                "Senha": hashed_password
            }
        )
        
        return ProfessorResponse(
            nome=new_professor.Nome,
            email=new_professor.Email,
            professor_id=new_professor.Professor_ID
        )
    
    async def update_professor(self, professor_id: int, professor_data: ProfessorUpdate) -> Optional[ProfessorResponse]:
        """Atualiza um professor existente"""
        # Verifica se o professor existe
        existing_professor = await self.prisma.professor.find_unique(
            where={"Professor_ID": professor_id}
        )
        
        if not existing_professor:
            return None
        
        # Prepara os dados para atualização
        update_data = {}
        
        if professor_data.nome is not None:
            update_data["Nome"] = professor_data.nome
        
        if professor_data.email is not None:
            # Verifica se o email já está em uso por outro professor
            if professor_data.email != existing_professor.Email:
                email_exists = await self.prisma.professor.find_unique(
                    where={"Email": professor_data.email}
                )
                if email_exists:
                    raise ValueError("Email já está em uso")
            update_data["Email"] = professor_data.email
        
        if professor_data.senha is not None:
            auth_service = AuthService()
            update_data["Senha"] = auth_service._hash_password(professor_data.senha)
        
        # Atualiza o professor
        updated_professor = await self.prisma.professor.update(
            where={"Professor_ID": professor_id},
            data=update_data
        )
        
        return ProfessorResponse(
            professor_id=updated_professor.Professor_ID,
            nome=updated_professor.Nome,
            email=updated_professor.Email
        )
    
    async def delete_professor(self, professor_id: int) -> bool:
        """Deleta um professor"""
        # Verifica se o professor existe
        existing_professor = await self.prisma.professor.find_unique(
            where={"Professor_ID": professor_id}
        )
        
        if not existing_professor:
            return False
        
        # Deleta o professor
        await self.prisma.professor.delete(
            where={"Professor_ID": professor_id}
        )
        
        return True
