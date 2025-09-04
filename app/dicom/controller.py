# app/dicom/controller.py

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import FileResponse, StreamingResponse
from typing import List
import io

from .schemas import DICOMCreate, DICOMResponse, DICOMSearch, DICOMPreviewURLResponse
from .service import DICOMService
from app.auth.auth_middleware import get_current_user
from app.auth.auth_schemas import UserResponse
from app.dependencies import get_dicom_service # Você precisará criar este dependency provider

router = APIRouter(prefix="/dicom", tags=["DICOM"])

@router.post("/upload", response_model=DICOMResponse, status_code=201)
async def upload_dicom_file(
    nome: str = File(...),
    paciente: str = File(...),
    files: List[UploadFile] = File(...),
    service: DICOMService = Depends(get_dicom_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Endpoint para fazer upload de múltiplos arquivos DICOM e seus metadados.
    O professor logado é associado automaticamente.
    """
    try:
        
        dicom_meta = DICOMCreate(nome=nome, paciente=paciente, professor_id=current_user.professor_id)
        return await service.create_dicom_upload(files, dicom_meta, current_user.professor_id)
    except IOError as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar arquivo: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{dicom_id}", response_class=FileResponse)
async def download_dicom_file(
    dicom_id: int,
    service: DICOMService = Depends(get_dicom_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Endpoint para baixar um arquivo DICOM pelo seu ID.
    Retorna o arquivo para download.
    """
    try:
        file_info = await service.get_dicom_file_by_id(dicom_id)
        if not file_info:
            raise HTTPException(status_code=404, detail="Arquivo DICOM não encontrado.")
        
        file_path, original_filename = file_info
        
        return FileResponse(
            path=file_path, 
            filename=f"{original_filename}.dcm", 
            media_type='application/dicom'
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/preview/{dicom_id}")
async def download_dicom_preview(
    dicom_id: int,
    service: DICOMService = Depends(get_dicom_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Endpoint para baixar a imagem de preview de um DICOM.
    Retorna a imagem diretamente do S3 como stream.
    """
    try:
        # Verificar se o DICOM existe e se o usuário tem acesso
        dicom = await service.get_dicom_by_id(dicom_id)
        if not dicom:
            raise HTTPException(status_code=404, detail="DICOM não encontrado.")
        
        # Verificar permissão
        if dicom.professor_id != current_user.professor_id:
            raise HTTPException(status_code=403, detail="Acesso não permitido a este recurso.")
        
        # Verificar se existe preview
        if not dicom.dicom_image_preview:
            raise HTTPException(status_code=404, detail="Imagem de preview não encontrada para este DICOM.")
        
        # Fazer download da imagem do S3
        image_data = await service.get_dicom_preview_image(dicom_id)
        if not image_data:
            raise HTTPException(status_code=404, detail="Erro ao carregar imagem de preview.")
        
        # Retornar como streaming response
        return StreamingResponse(
            io.BytesIO(image_data),
            media_type="image/png",
            headers={
                "Content-Disposition": f"inline; filename=preview_{dicom_id}.png",
                "Cache-Control": "public, max-age=3600"  # Cache por 1 hora
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.get("/preview/{dicom_id}/url", response_model=DICOMPreviewURLResponse)
async def get_dicom_preview_url(
    dicom_id: int,
    service: DICOMService = Depends(get_dicom_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Endpoint para obter a URL de download da imagem de preview de um DICOM.
    Retorna uma URL pré-assinada do S3.
    """
    try:
        # Verificar se o DICOM existe e se o usuário tem acesso
        dicom = await service.get_dicom_by_id(dicom_id)
        if not dicom:
            raise HTTPException(status_code=404, detail="DICOM não encontrado.")
        
        # Verificar permissão
        if dicom.professor_id != current_user.professor_id:
            raise HTTPException(status_code=403, detail="Acesso não permitido a este recurso.")
        
        # Verificar se existe preview
        if not dicom.dicom_image_preview:
            raise HTTPException(status_code=404, detail="Imagem de preview não encontrada para este DICOM.")
        
        # Gerar URL pré-assinada
        preview_url = await service.get_dicom_preview_download_url(dicom_id)
        if not preview_url:
            raise HTTPException(status_code=404, detail="Erro ao gerar URL de preview.")
        
        return DICOMPreviewURLResponse(
            dicom_id=dicom_id,
            preview_url=preview_url,
            expires_in=3600  # URL válida por 1 hora
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.get("/", response_model=List[DICOMResponse])
async def list_user_dicoms(
    service: DICOMService = Depends(get_dicom_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """Retorna uma lista com os metadados de todos os arquivos DICOM do usuário logado."""
    try:
        return await service.get_dicoms_by_professor_id(current_user.professor_id)
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
    
@router.get("/{dicom_id}", response_model=DICOMResponse)
async def get_dicom_by_id(
    dicom_id: int,
    service: DICOMService = Depends(get_dicom_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Retorna os metadados de um arquivo DICOM específico pelo seu ID.
    O acesso é restrito ao professor que fez o upload.
    """
    try:
        dicom = await service.get_dicom_by_id(dicom_id)

        if not dicom:
            raise HTTPException(status_code=404, detail="Arquivo DICOM não encontrado.")

        # Verificação de segurança: Apenas o dono do arquivo pode vê-lo
        if dicom.professor_id != current_user.professor_id:
            raise HTTPException(status_code=403, detail="Acesso não permitido a este recurso.")

        return dicom
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))    