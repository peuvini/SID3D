# arquivo3D/controller.py

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from typing import List, Optional

from .schemas import (
    Arquivo3DResponse, ConversionRequest, DownloadURLResponse, FileFormat,
    SlicePlane, VolumeDimensionsResponse, EditRequest
)
from .service import Arquivo3DService
from app.auth.auth_middleware import get_current_user
from app.auth.auth_schemas import UserResponse
from app.dependencies import get_arquivo3d_service

router = APIRouter(prefix="/arquivo3d", tags=["Arquivo 3D"])

@router.post("/convert", response_model=Arquivo3DResponse, status_code=201)
async def converter_dicom(
    conversion_request: ConversionRequest,
    service: Arquivo3DService = Depends(get_arquivo3d_service),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Converte uma série DICOM em um arquivo 3D.
    
    - **dicom_id**: ID do registro DICOM para conversão
    - **file_format**: Formato desejado (STL, OBJ, PLY)
    
    Inicia o processo de geração, upload e salvamento do arquivo 3D.
    """
    try:
        return await service.converter_dicom_para_3d(
            conversion_request, 
            current_user.professor_id
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/", response_model=List[Arquivo3DResponse])
async def get_all_files(
    only_mine: bool = Query(False, description="Mostrar apenas meus arquivos 3D"),
    service: Arquivo3DService = Depends(get_arquivo3d_service),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Lista todos os arquivos 3D.
    
    - **only_mine**: Se True, mostra apenas os arquivos 3D do usuário atual
    """
    user_id = current_user.professor_id if only_mine else None
    return await service.get_all_files(user_id)

@router.get("/dicom/{dicom_id}", response_model=List[Arquivo3DResponse])
async def get_files_by_dicom(
    dicom_id: int,
    service: Arquivo3DService = Depends(get_arquivo3d_service),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Lista todos os arquivos 3D associados a um DICOM específico.
    
    - **dicom_id**: ID do registro DICOM
    """
    try:
        return await service.get_files_by_dicom_id(dicom_id, current_user.professor_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/{arquivo_id}", response_model=Arquivo3DResponse)
async def get_file_by_id(
    arquivo_id: int,
    service: Arquivo3DService = Depends(get_arquivo3d_service),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Obtém um arquivo 3D específico pelo ID.
    """
    arquivo = await service.get_file_by_id(arquivo_id)
    if not arquivo:
        raise HTTPException(status_code=404, detail="Arquivo 3D não encontrado")
    return arquivo

@router.get("/download/{arquivo_id}", response_model=DownloadURLResponse)
async def get_download_url(
    arquivo_id: int,
    service: Arquivo3DService = Depends(get_arquivo3d_service),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Obtém uma URL pré-assinada para download de um arquivo 3D.
    
    - **arquivo_id**: ID do arquivo 3D
    """
    try:
        arquivo = await service.get_file_by_id(arquivo_id)
        if not arquivo:
            raise HTTPException(status_code=404, detail="Arquivo 3D não encontrado")
            
        download_url = await service.get_download_url(arquivo_id, current_user.professor_id)
        if not download_url:
            raise HTTPException(status_code=404, detail="Não foi possível gerar URL de download")
        
        return DownloadURLResponse(
            url=download_url, 
            expires_in=3600,
            file_format=arquivo.file_format
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/view/{arquivo_id}")
async def view_file(
    arquivo_id: int,
    service: Arquivo3DService = Depends(get_arquivo3d_service),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Visualiza/baixa um arquivo 3D diretamente.
    
    Retorna o conteúdo binário do arquivo com o content-type apropriado.
    """
    try:
        # Primeiro obtém as informações do arquivo para determinar o content-type
        arquivo_info = await service.get_file_by_id(arquivo_id)
        if not arquivo_info:
            raise HTTPException(status_code=404, detail="Arquivo 3D não encontrado")
        
        # Obtém o conteúdo do arquivo
        file_content = await service.get_file_content(arquivo_id, current_user.professor_id)
        
        # Define o content-type baseado no formato
        content_types = {
            FileFormat.STL: "model/stl",
            FileFormat.OBJ: "model/obj", 
            FileFormat.PLY: "model/ply"
        }
        content_type = content_types.get(arquivo_info.file_format, "application/octet-stream")
        
        # Define o nome do arquivo para download
        filename = f"arquivo3d_{arquivo_id}.{arquivo_info.file_format.value}"
        
        return Response(
            content=file_content,
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.delete("/{arquivo_id}", status_code=204)
async def delete_file(
    arquivo_id: int,
    service: Arquivo3DService = Depends(get_arquivo3d_service),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Deleta um arquivo 3D e remove do S3.
    
    Apenas o professor que criou o arquivo (dono do DICOM) pode deletá-lo.
    """
    try:
        deleted = await service.delete_file(arquivo_id, current_user.professor_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Arquivo 3D não encontrado")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")
    


@router.get("/volume/dimensions/{dicom_id}", response_model=VolumeDimensionsResponse)
async def get_volume_dimensions(
    dicom_id: int,
    service: Arquivo3DService = Depends(get_arquivo3d_service),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Retorna as dimensões e o número máximo de fatias para cada plano
    (axial, coronal, sagital) de uma série DICOM.
    """
    try:
        return await service.get_volume_dimensions(dicom_id, current_user.professor_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {e}")

@router.get("/slice/{dicom_id}",
            responses={200: {"content": {"image/png": {}}}},
            response_class=Response)
async def get_slice_image(
    dicom_id: int,
    plane: SlicePlane = Query(..., description="Plano de corte: axial, sagital ou coronal"),
    index: int = Query(..., description="Índice da fatia desejada"),
    service: Arquivo3DService = Depends(get_arquivo3d_service),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Obtém uma imagem PNG de uma fatia específica de uma série DICOM.
    """
    try:
        image_bytes = await service.get_slice_image(
            dicom_id, current_user.professor_id, plane.value, index
        )
        return Response(content=image_bytes, media_type="image/png")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {e}")
    
@router.post("/{arquivo_id}/edit", response_model=Arquivo3DResponse, status_code=201)
async def edit_file(
    arquivo_id: int,
    edit_request: EditRequest,
    service: Arquivo3DService = Depends(get_arquivo3d_service),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Edita um arquivo 3D existente usando uma operação booleana com uma caixa.
    
    Cria um *novo* arquivo 3D com o resultado da edição.
    
    - **operation**: 'intersect' (manter o que está dentro da caixa) ou 'difference' (remover o que está dentro).
    - **box_center**: Coordenadas [x, y, z] do centro da caixa.
    - **box_size**: Dimensões [largura, profundidade, altura] da caixa.
    """
    try:
        return await service.edit_3d_file(
            original_arquivo_id=arquivo_id,
            user_id=current_user.professor_id,
            edit_params=edit_request
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno no endpoint de edição: {e}")