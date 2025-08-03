from pydantic import BaseModel, EmailStr
from typing import Optional


class ProfessorBase(BaseModel):
    """Schema base para professor"""
    nome: str
    email: EmailStr


class ProfessorCreate(ProfessorBase):
    """Schema para criação de professor"""
    senha: str


class ProfessorUpdate(BaseModel):
    """Schema para atualização de professor"""
    nome: Optional[str] = None
    email: Optional[EmailStr] = None
    senha: Optional[str] = None


class ProfessorResponse(ProfessorBase):
    """Schema para resposta de professor"""
    professor_id: int
    
    class Config:
        from_attributes = True
