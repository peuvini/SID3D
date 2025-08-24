from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class ProfessorBase(BaseModel):
    """Schema base para professor"""
    nome: str = Field(..., description="Nome completo do professor", min_length=2, max_length=100)
    email: EmailStr = Field(..., description="Email do professor")

class ProfessorCreate(ProfessorBase):
    """Schema para criação de professor"""
    senha: str = Field(..., description="Senha do professor", min_length=6)

class ProfessorUpdate(BaseModel):
    """Schema para atualização de professor"""
    nome: Optional[str] = Field(None, description="Novo nome do professor", min_length=2, max_length=100)
    email: Optional[EmailStr] = Field(None, description="Novo email do professor")
    senha: Optional[str] = Field(None, description="Nova senha do professor", min_length=6)

class ProfessorResponse(ProfessorBase):
    """Schema para resposta de professor"""
    professor_id: int = Field(..., description="ID único do professor")
    created_at: Optional[str] = Field(None, description="Data de criação do registro")
    
    class Config:
        from_attributes = True

class ProfessorSearch(BaseModel):
    """Schema para busca de professores"""
    nome: Optional[str] = Field(None, description="Buscar por nome (busca parcial)")
    email: Optional[str] = Field(None, description="Buscar por email (busca parcial)")

class PasswordChangeRequest(BaseModel):
    """Schema para mudança de senha"""
    senha_atual: str = Field(..., description="Senha atual")
    nova_senha: str = Field(..., description="Nova senha", min_length=6)
