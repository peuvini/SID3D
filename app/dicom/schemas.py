from pydantic import BaseModel, Field
from typing import Optional, List

class DICOMBase(BaseModel):
    """Schema base para metadados de um arquivo DICOM."""
    nome: str = Field(..., description="Nome do exame DICOM")
    paciente: str = Field(..., description="Nome do paciente")

# Schema para a criação de um novo registro DICOM
class DICOMCreate(DICOMBase):
    """Schema para receber os metadados durante o upload de um arquivo DICOM."""
    pass

# Schema para a atualização de um registro DICOM
class DICOMUpdate(BaseModel):
    """Schema para atualizar os metadados de um arquivo DICOM."""
    nome: Optional[str] = Field(None, description="Nome do exame DICOM")
    paciente: Optional[str] = Field(None, description="Nome do paciente")

# Schema para representar a busca, usando query params
class DICOMSearch(BaseModel):
    """Schema para os parâmetros de busca de arquivos DICOM."""
    nome: Optional[str] = Field(None, description="Filtrar por nome do exame")
    paciente: Optional[str] = Field(None, description="Filtrar por nome do paciente")

# Schema de resposta, retornado pela API
class DICOMResponse(DICOMBase):
    """Schema para a resposta da API com os dados completos de um DICOM."""
    dicom_id: int = Field(..., description="ID único do registro DICOM")
    professor_id: int = Field(..., description="ID do professor responsável")
    urls: List[str] = Field(default_factory=list, description="URLs dos arquivos DICOM no S3")
    created_at: Optional[str] = Field(None, description="Data de criação do registro")

    class Config:
        from_attributes = True

class DownloadURLResponse(BaseModel):
    """Schema de resposta para a URL de download pré-assinada."""
    url: str = Field(..., description="URL pré-assinada para download")
    expires_in: int = Field(default=3600, description="Tempo de expiração em segundos")