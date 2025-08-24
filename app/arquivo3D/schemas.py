from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class FileFormat(str, Enum):
    """Formatos de arquivo 3D suportados."""
    STL = "stl"
    OBJ = "obj"
    PLY = "ply"

class Arquivo3DBase(BaseModel):
    """Schema base para os metadados de um arquivo 3D."""
    dicom_id: int = Field(..., description="ID do registro DICOM original")
    file_format: FileFormat = Field(default=FileFormat.STL, description="Formato do arquivo 3D")

class Arquivo3DCreate(Arquivo3DBase):
    """Schema para a criação de um novo arquivo 3D."""
    pass

class Arquivo3DUpdate(BaseModel):
    """Schema para atualização de metadados de um arquivo 3D."""
    file_format: Optional[FileFormat] = Field(None, description="Novo formato do arquivo")

class Arquivo3DResponse(Arquivo3DBase):
    """Schema para a resposta da API com os dados completos de um arquivo 3D."""
    id: int = Field(..., description="ID único do arquivo 3D")
    url: str = Field(..., description="URL do arquivo no S3")
    version: int = Field(..., description="Versão do arquivo")
    professor_id: int = Field(..., description="ID do professor responsável")
    created_at: Optional[str] = Field(None, description="Data de criação")
    file_size: Optional[int] = Field(None, description="Tamanho do arquivo em bytes")

    class Config:
        from_attributes = True

class DownloadURLResponse(BaseModel):
    """Schema de resposta para a URL de download pré-assinada."""
    url: str = Field(..., description="URL pré-assinada para download")
    expires_in: int = Field(default=3600, description="Tempo de expiração em segundos")
    file_format: FileFormat = Field(..., description="Formato do arquivo")

class ConversionRequest(BaseModel):
    """Schema para requisição de conversão DICOM para 3D."""
    dicom_id: int = Field(..., description="ID do registro DICOM para conversão")
    file_format: FileFormat = Field(default=FileFormat.STL, description="Formato desejado para o arquivo 3D")