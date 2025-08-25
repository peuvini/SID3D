from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Query
from typing import List, Optional
from .schemas import DICOMCreate, DICOMResponse, DICOMSearch, DICOMUpdate, DownloadURLResponse
from .service import DICOMService
from app.auth.auth_middleware import get_current_user
from app.auth.auth_schemas import UserResponse
from app.dependencies import get_dicom_service
router = APIRouter(prefix="/dicom", tags=["DICOM"])

@router.post("/upload", response_model=DICOMResponse, status_code=201)
async def upload_dicom_files(
    files: List[UploadFile] = File(..., description="Arquivos DICOM para upload"),
    nome: str = Form(..., description="Nome do exame DICOM"),
    paciente: str = Form(..., description="Nome do paciente"),
    service: DICOMService = Depends(get_dicom_service),
    current_user: UserResponse = Depends(get_current_user),
):
    dicom_data = DICOMCreate(nome=nome, paciente=paciente)
    try:
        return await service.create_dicom_upload(files, dicom_data, current_user.professor_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/", response_model=List[DICOMResponse])
async def get_all_dicoms(
    only_mine: bool = Query(False, description="Mostrar apenas meus DICOMs"),
    service: DICOMService = Depends(get_dicom_service),
    current_user: UserResponse = Depends(get_current_user),
):
    user_id = current_user.professor_id if only_mine else None
    return await service.get_all_dicoms(user_id)

@router.get("/search", response_model=List[DICOMResponse])
async def search_dicoms(
    nome: Optional[str] = Query(None, description="Filtrar por nome do exame"),
    paciente: Optional[str] = Query(None, description="Filtrar por nome do paciente"),
    only_mine: bool = Query(False, description="Buscar apenas em meus DICOMs"),
    service: DICOMService = Depends(get_dicom_service),
    current_user: UserResponse = Depends(get_current_user),
):
    search_params = DICOMSearch(nome=nome, paciente=paciente)
    user_id = current_user.professor_id if only_mine else None
    return await service.search_dicoms(search_params, user_id)

@router.get("/{dicom_id}", response_model=DICOMResponse)
async def get_dicom_by_id(
    dicom_id: int,
    service: DICOMService = Depends(get_dicom_service),
    current_user: UserResponse = Depends(get_current_user),
):
    dicom = await service.get_dicom_by_id(dicom_id)
    if not dicom:
        raise HTTPException(status_code=404, detail="Registro DICOM não encontrado")
    return dicom

@router.put("/{dicom_id}", response_model=DICOMResponse)
async def update_dicom(
    dicom_id: int,
    update_data: DICOMUpdate,
    service: DICOMService = Depends(get_dicom_service),
    current_user: UserResponse = Depends(get_current_user),
):
    try:
        updated_dicom = await service.update_dicom(dicom_id, update_data, current_user.professor_id)
        if not updated_dicom:
            raise HTTPException(status_code=404, detail="Registro DICOM não encontrado")
        return updated_dicom
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/download/{dicom_id}", response_model=DownloadURLResponse)
async def get_dicom_download_url(
    dicom_id: int,
    file_index: int = Query(0, ge=0, description="Índice do arquivo (0 para o primeiro)"),
    service: DICOMService = Depends(get_dicom_service),
    current_user: UserResponse = Depends(get_current_user),
):
    try:
        download_url = await service.get_dicom_download_url(dicom_id, file_index)
        if not download_url:
            raise HTTPException(status_code=404, detail="Arquivo DICOM não encontrado ou índice inválido")
        return DownloadURLResponse(url=download_url, expires_in=3600)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.delete("/{dicom_id}", status_code=204)
async def delete_dicom(
    dicom_id: int,
    service: DICOMService = Depends(get_dicom_service),
    current_user: UserResponse = Depends(get_current_user),
):
    try:
        deleted = await service.delete_dicom_by_id(dicom_id, current_user.professor_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Registro DICOM não encontrado")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")