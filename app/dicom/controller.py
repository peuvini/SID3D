from fastapi import APIRouter, HTTPException, Depends, UploadFile, File

from typing import List

from .schemas import DICOMCreate, DICOMResponse, DICOMSearch, DownloadURLResponse
from .service import DICOMService
from app.auth.auth_middleware import get_current_user
from app.auth.auth_schemas import UserResponse
from app.dependencies import get_dicom_service # Você precisará criar este dependency provider

router = APIRouter(prefix="/dicom", tags=["DICOM"])

@router.post("/upload", response_model=DICOMResponse, status_code=201)
async def upload_dicom_file(
    dicom_meta: DICOMCreate = Depends(),
    file: UploadFile = File(...),
    service: DICOMService = Depends(get_dicom_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Endpoint para fazer upload de um arquivo DICOM e seus metadados.
    O professor logado é associado automaticamente.
    """
    try:
        # Garante que o ID do professor no DTO corresponda ao usuário logado
        if dicom_meta.professor_id != current_user.professor_id:
            raise HTTPException(status_code=403, detail="Operação não permitida. O professor_id deve ser o do usuário logado.")
            
        return await service.create_dicom_upload(file, dicom_meta)
    except IOError as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar arquivo: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{dicom_id}", response_model=DownloadURLResponse)
async def get_dicom_download_url(
    dicom_id: int,
    service: DICOMService = Depends(get_dicom_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Endpoint para obter uma URL segura e temporária para baixar um arquivo DICOM.
    """
    try:
        download_url = await service.get_dicom_download_url(dicom_id)
        if not download_url:
            raise HTTPException(status_code=404, detail="Arquivo DICOM não encontrado.")

        return DownloadURLResponse(url=download_url)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[DICOMResponse])
async def list_all_dicoms(
    service: DICOMService = Depends(get_dicom_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """Retorna uma lista com os metadados de todos os arquivos DICOM."""
    try:
        return await service.get_all_dicoms()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", response_model=List[DICOMResponse])
async def search_dicoms(
    search_params: DICOMSearch = Depends(),
    service: DICOMService = Depends(get_dicom_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Busca arquivos DICOM com base em parâmetros de query (nome, paciente, professor_id).
    """
    try:
        return await service.search_dicoms(search_params)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{dicom_id}", status_code=204)
async def delete_dicom_file(
    dicom_id: int,
    service: DICOMService = Depends(get_dicom_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Deleta um arquivo DICOM e seus metadados.
    Apenas o professor que fez o upload pode deletar.
    """
    try:
        success = await service.delete_dicom_by_id(dicom_id, current_user.professor_id)
        if not success:
            raise HTTPException(status_code=404, detail="Arquivo DICOM não encontrado.")
        return # Retorna 204 No Content
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))