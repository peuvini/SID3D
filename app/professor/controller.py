from fastapi import APIRouter, HTTPException, Depends
from .service import ProfessorService
from .schemas import ProfessorCreate, ProfessorUpdate, ProfessorResponse
from app.auth.auth_middleware import require_auth, get_current_user
from app.auth.auth_schemas import UserResponse
from app.dependencies import get_professor_service

router = APIRouter(prefix="/professor", tags=["Professor"])


@router.get("/", response_model=list[ProfessorResponse])
async def get_professores(
    service: ProfessorService = Depends(get_professor_service), 
    current_user: UserResponse = Depends(get_current_user)
):
    """Retorna todos os professores (apenas para usuários autenticados)"""
    try:
        return await service.get_all_professores()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{professor_id}", response_model=ProfessorResponse)
async def get_professor_by_id(
    professor_id: int, 
    service: ProfessorService = Depends(get_professor_service), 
    current_user: UserResponse = Depends(get_current_user)
):
    """Retorna um professor específico por ID"""
    try:
        professor = await service.get_professor_by_id(professor_id)
        if not professor:
            raise HTTPException(status_code=404, detail="Professor não encontrado")
        return professor
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=ProfessorResponse)
async def create_professor(
    professor: ProfessorCreate,
    service: ProfessorService = Depends(get_professor_service), 
    current_user: UserResponse = Depends(get_current_user)
):
    """Cria um novo professor"""
    try:
        return await service.create_professor(professor)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{professor_id}", response_model=ProfessorResponse)
async def update_professor(
    professor_id: int,
    professor: ProfessorUpdate,
    service: ProfessorService = Depends(get_professor_service),
    current_user: UserResponse = Depends(get_current_user)
):
    """Atualiza um professor existente"""
    # Verificação de autorização
    if current_user.professor_id != professor_id:
         raise HTTPException(status_code=403, detail="Operação não permitida")
    
    try:
        updated_professor = await service.update_professor(professor_id, professor)
        if not updated_professor:
            raise HTTPException(status_code=404, detail="Professor não encontrado")
        return updated_professor
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{professor_id}")
async def delete_professor(
    professor_id: int,
    service: ProfessorService = Depends(get_professor_service),
    current_user: UserResponse = Depends(get_current_user)
):
    """Deleta um professor"""

    # Verificação de autorização
    if current_user.professor_id != professor_id:
         raise HTTPException(status_code=403, detail="Operação não permitida")

    try:
        success = await service.delete_professor(professor_id)
        if not success:
            raise HTTPException(status_code=404, detail="Professor não encontrado")
        return {"message": "Professor removido com sucesso"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
