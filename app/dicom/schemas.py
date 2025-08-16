# app/dicom/schemas.py

from pydantic import BaseModel
from typing import Optional

# Schema base para os dados de um arquivo DICOM
class DICOMBase(BaseModel):
    """Schema base para metadados de um arquivo DICOM."""
    nome: str
    paciente: str
    # O URL será gerenciado internamente pelo serviço ao fazer o upload
    url: Optional[str] = None 

# Schema para a criação de um novo registro DICOM
# O controller receberá esses dados junto com o arquivo.
class DICOMCreate(BaseModel):
    """Schema para receber os metadados durante o upload de um arquivo DICOM."""
    nome: str
    paciente: str
    professor_id: int

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
    professor_id: Optional[int] = None

# Schema de resposta, retornado pela API
class DICOMResponse(DICOMBase):
    """Schema para a resposta da API com os dados completos de um DICOM."""
    dicom_id: int
    professor_id: int

    class Config:
        from_attributes = True # Permite mapear diretamente de modelos ORM

# O diagrama menciona um DICOMFile com bytes.
# Em FastAPI, o retorno de arquivos é geralmente tratado com StreamingResponse
# ou FileResponse, então um schema Pydantic para o arquivo em si não é necessário.
# O controller cuidará do tipo de resposta apropriado.