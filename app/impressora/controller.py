# app/impressora/controller.py

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from .schemas import ImpressoraCreate, ImpressoraResponse, ImprimirRequest, ImpressaoResponse
from .service import ImpressoraService
from app.auth.auth_middleware import get_current_user
from app.auth.auth_schemas import UserResponse
from app.dependencies import get_impressora_service # Crie este provider de dependência

router = APIRouter(prefix="/impressoras", tags=["Impressoras"])


@router.post("/", response_model=ImpressoraResponse, status_code=status.HTTP_201_CREATED)
async def cadastrar_impressora(
    impressora_data: ImpressoraCreate,
    service: ImpressoraService = Depends(get_impressora_service),
    current_user: UserResponse = Depends(get_current_user) # TODO: Adicionar lógica de permissão se necessário
):
    """Cadastra uma nova impressora 3D no sistema."""
    try:
        return await service.cadastrar_impressora(impressora_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/", response_model=List[ImpressoraResponse])
async def listar_impressoras(
    service: ImpressoraService = Depends(get_impressora_service),
    current_user: UserResponse = Depends(get_current_user)
):
    """Lista todas as impressoras cadastradas."""
    try:
        return await service.get_all_impressoras()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/imprimir", response_model=ImpressaoResponse, status_code=status.HTTP_202_ACCEPTED)
async def imprimir_arquivo(
    request: ImprimirRequest,
    service: ImpressoraService = Depends(get_impressora_service),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Inicia um trabalho de impressão de um arquivo 3D em uma impressora específica.
    Retorna o registro do trabalho de impressão criado.
    """
    try:
        job = await service.iniciar_impressao(request)
        return job
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))