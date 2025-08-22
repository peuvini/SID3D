from pydantic import BaseModel
from typing import Optional

class DICOMBase(BaseModel):
    """Schema base para metadados de um arquivo DICOM."""
    nome: str
    paciente: str
    # O URL será gerenciado internamente pelo serviço ao fazer o upload
    url: Optional[str] = None 

# Schema para a criação de um novo registro DICOM
class DICOMCreate(BaseModel):
    """Schema para receber os metadados durante o upload de um arquivo DICOM."""
    nome: str
    paciente: str

# Schema para a atualização de um registro DICOM
class DICOMUpdate(BaseModel):
    """Schema para atualizar os metadados de um arquivo DICOM."""
    nome: Optional[str] = None
    paciente: Optional[str] = None

# Schema para representar a busca, usando query params
class DICOMSearch(BaseModel):
    """Schema para os parâmetros de busca de arquivos DICOM."""
    nome: Optional[str] = None
    paciente: Optional[str] = None

# Schema de resposta, retornado pela API
class DICOMResponse(DICOMBase):
    """Schema para a resposta da API com os dados completos de um DICOM."""
    dicom_id: int
    professor_id: int

    class Config:
        from_attributes = True # Permite mapear diretamente de modelos ORM
class DownloadURLResponse(BaseModel):
    """Schema de resposta para a URL de download pré-assinada."""
    url: str