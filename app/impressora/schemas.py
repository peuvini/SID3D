# app/impressora/schemas.py

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# ==================== Impressora ====================

class ImpressoraBase(BaseModel):
    """Schema base para uma impressora."""
    nome: str = Field(..., description="Nome da impressora")
    modelo: str = Field(..., description="Modelo da impressora")

class ImpressoraCreate(ImpressoraBase):
    """Schema para cadastrar uma nova impressora."""
    status: Optional[str] = Field(default="disponivel", description="Status inicial da impressora")

class ImpressoraUpdate(BaseModel):
    """Schema para atualizar uma impressora existente."""
    nome: Optional[str] = None
    modelo: Optional[str] = None
    status: Optional[str] = None

class ImpressoraResponse(ImpressoraBase):
    """Schema para a resposta da API com os dados de uma impressora."""
    id: int = Field(..., description="ID único da impressora")
    status: str = Field(..., description="Status atual da impressora")
    created_at: datetime = Field(..., description="Data de criação do registro")
    updated_at: datetime = Field(..., description="Data da última atualização")

    class Config:
        from_attributes = True

# ==================== Impressao3D (Trabalho de Impressão) ====================

class Impressao3DBase(BaseModel):
    """Schema base para um trabalho de impressão 3D."""
    arquivo3d_id: int = Field(..., description="ID do arquivo 3D a ser impresso")
    impressora_id: int = Field(..., description="ID da impressora que realizará o trabalho")

class Impressao3DCreate(Impressao3DBase):
    """Schema para iniciar um novo trabalho de impressão."""
    data_inicio: datetime = Field(default_factory=datetime.now, description="Data/hora de início da impressão")

class Impressao3DUpdate(BaseModel):
    """Schema para atualizar um trabalho de impressão."""
    status: Optional[str] = None
    data_conclusao: Optional[datetime] = None

class Impressao3DResponse(Impressao3DBase):
    """Schema de resposta para um trabalho de impressão, servindo como um log."""
    id: int = Field(..., description="ID único do trabalho de impressão")
    data_inicio: datetime = Field(..., description="Data/hora de início da impressão")
    data_conclusao: Optional[datetime] = Field(None, description="Data/hora de conclusão da impressão")
    status: str = Field(default="pendente", description="Status do trabalho: pendente, em_andamento, concluido, falhou")
    created_at: datetime = Field(..., description="Data de criação do registro")
    updated_at: datetime = Field(..., description="Data da última atualização")

    class Config:
        from_attributes = True

# ==================== DTO para Ação de Imprimir ====================

class ImprimirRequest(BaseModel):
    """Schema para a requisição da ação de imprimir."""
    impressora_id: int
    arquivo_id: int