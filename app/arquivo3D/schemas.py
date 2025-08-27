from pydantic import BaseModel, Field
from typing import Optional, Tuple
from enum import Enum
from datetime import datetime

class SlicePlane(str, Enum):
    """Planos de corte para visualização de fatias."""
    AXIAL = "axial"
    SAGITTAL = "sagittal"
    CORONAL = "coronal"

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
    file_size: Optional[int] = Field(None, description="Tamanho do arquivo em bytes")

class Arquivo3DUpdate(BaseModel):
    """Schema para atualização de metadados de um arquivo 3D."""
    file_format: Optional[FileFormat] = Field(None, description="Novo formato do arquivo")
    file_size: Optional[int] = Field(None, description="Tamanho do arquivo em bytes")

class Arquivo3DResponse(Arquivo3DBase):
    """Schema para a resposta da API com os dados completos de um arquivo 3D."""
    id: int = Field(..., description="ID único do arquivo 3D")
    s3_url: str = Field(..., description="URL do arquivo no S3")
    file_size: Optional[int] = Field(None, description="Tamanho do arquivo em bytes")
    created_at: datetime = Field(..., description="Data de criação")
    updated_at: datetime = Field(..., description="Data da última atualização")

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

    iso_value: Optional[float] = Field(None, description="Valor de isovalor (Hounsfield Units) para extração da superfície. Ex: 300 para osso.")
    simplify_target_faces: Optional[int] = Field(None, description="Número de faces para simplificar a malha final. Menos faces = menor detalhe, menor arquivo.")


# NOVO Schema para as dimensões do volume
class VolumeDimensionsResponse(BaseModel):
    """Schema de resposta para as dimensões do volume 3D."""
    dicom_id: int = Field(..., description="ID do registro DICOM")
    axial_slices: int = Field(..., description="Número de fatias no plano Axial (profundidade)")
    coronal_slices: int = Field(..., description="Número de fatias no plano Coronal (altura)")
    sagittal_slices: int = Field(..., description="Número de fatias no plano Sagital (largura)")
    dimensions: Tuple[int, int, int] = Field(..., description="Dimensões (profundidade, altura, largura)")


class EditOperation(str, Enum):
    """Define a operação de edição a ser realizada."""
    INTERSECT = "intersect" # Manter apenas o que está DENTRO da área de interesse
    DIFFERENCE = "difference" # Remover o que está DENTRO da área de interesse
class EditRequest(BaseModel):
    """Schema para a requisição de edição de um arquivo 3D."""
    operation: EditOperation = Field(..., description="A operação booleana a ser aplicada (intersect ou difference)")
    box_center: Tuple[float, float, float] = Field(..., description="As coordenadas [x, y, z] do centro da caixa de seleção.")
    box_size: Tuple[float, float, float] = Field(..., description="As dimensões [largura, profundidade, altura] da caixa de seleção.")
    new_file_format: Optional[FileFormat] = Field(default=None, description="Formato do novo arquivo. Se omitido, usa o formato do original.")