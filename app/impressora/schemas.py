# app/impressora/schemas.py

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# ==================== Impressora ====================

class ImpressoraBase(BaseModel):
    """Schema base para uma impressora."""
    nome: str
    ip: str = Field(..., description="Endereço IP da impressora na rede local.")

class ImpressoraCreate(ImpressoraBase):
    """Schema para cadastrar uma nova impressora."""
    pass

class ImpressoraUpdate(BaseModel):
    """Schema para atualizar uma impressora existente."""
    nome: Optional[str] = None
    ip: Optional[str] = None

class ImpressoraResponse(ImpressoraBase):
    """Schema para a resposta da API com os dados de uma impressora."""
    id: int # Usando int como no exemplo do Professor para consistência

    class Config:
        from_attributes = True

# ==================== Impressao (Trabalho de Impressão) ====================

class ImpressaoBase(BaseModel):
    """Schema base para um trabalho de impressão."""
    impressora_id: int
    # No diagrama, 'Arquivo3D' é similar ao 'DICOM'. Assumimos que ele tem um ID.
    arquivo_3d_id: int 

class ImpressaoCreate(ImpressaoBase):
    """Schema para iniciar um novo trabalho de impressão."""
    pass

class ImpressaoResponse(ImpressaoBase):
    """Schema de resposta para um trabalho de impressão, servindo como um log."""
    id: int
    data_inicio: datetime
    data_conclusao: Optional[datetime] = None
    status: str # Ex: "iniciada", "concluida", "falhou"

    class Config:
        from_attributes = True

# ==================== DTO para Ação de Imprimir ====================

class ImprimirRequest(BaseModel):
    """Schema para a requisição da ação de imprimir."""
    impressora_id: int
    arquivo_id: int