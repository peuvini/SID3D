from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from .service import ProfessorService
from .schemas import ProfessorCreate, ProfessorUpdate, ProfessorResponse, ProfessorSearch, PasswordChangeRequest
from app.auth.auth_middleware import get_current_user
from app.auth.auth_schemas import UserResponse
from app.dependencies import get_professor_service

router = APIRouter(prefix="/professor", tags=["Professor"])

@router.get("/", response_model=List[ProfessorResponse])
async def get_all_professores(
    service: ProfessorService = Depends(get_professor_service), 
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Lista todos os professores.
    
    Apenas para usuários autenticados.
    """
    try:
        return await service.get_all_professores()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/search", response_model=List[ProfessorResponse])
async def search_professores(
    nome: Optional[str] = Query(None, description="Buscar por nome (busca parcial)"),
    email: Optional[str] = Query(None, description="Buscar por email (busca parcial)"),
    service: ProfessorService = Depends(get_professor_service),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Busca professores com base nos parâmetros fornecidos.
    
    - **nome**: Filtro por nome (busca parcial, case-insensitive)
    - **email**: Filtro por email (busca parcial, case-insensitive)
    """
    search_params = ProfessorSearch(nome=nome, email=email)
    try:
        return await service.search_professores(search_params)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/me", response_model=ProfessorResponse)
async def get_my_profile(
    service: ProfessorService = Depends(get_professor_service),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Retorna o perfil do professor autenticado.
    """
    try:
        professor = await service.get_professor_by_id(current_user.professor_id)
        if not professor:
            raise HTTPException(status_code=404, detail="Perfil não encontrado")
        return professor
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/statistics")
async def get_statistics(
    service: ProfessorService = Depends(get_professor_service),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Retorna estatísticas dos professores.
    """
    try:
        return await service.get_statistics()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/{professor_id}", response_model=ProfessorResponse)
async def get_professor_by_id(
    professor_id: int, 
    service: ProfessorService = Depends(get_professor_service), 
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Retorna um professor específico por ID.
    """
    try:
        professor = await service.get_professor_by_id(professor_id)
        if not professor:
            raise HTTPException(status_code=404, detail="Professor não encontrado")
        return professor
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.post("/", response_model=ProfessorResponse, status_code=201)
async def create_professor(
    professor: ProfessorCreate,
    service: ProfessorService = Depends(get_professor_service), 
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Cria um novo professor.
    
    - **nome**: Nome completo do professor
    - **email**: Email válido e único
    - **senha**: Senha com pelo menos 6 caracteres
    """
    try:
        return await service.create_professor(professor)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.put("/{professor_id}", response_model=ProfessorResponse)
async def update_professor(
    professor_id: int,
    professor: ProfessorUpdate,
    service: ProfessorService = Depends(get_professor_service),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Atualiza um professor existente.
    
    Apenas o próprio professor pode atualizar seu perfil.
    """
    try:
        updated_professor = await service.update_professor(professor_id, professor, current_user.professor_id)
        if not updated_professor:
            raise HTTPException(status_code=404, detail="Professor não encontrado")
        return updated_professor
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.put("/{professor_id}/password", status_code=200)
async def change_password(
    professor_id: int,
    password_data: PasswordChangeRequest,
    service: ProfessorService = Depends(get_professor_service),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Altera a senha de um professor.
    
    Apenas o próprio professor pode alterar sua senha.
    """
    try:
        success = await service.change_password(professor_id, password_data, current_user.professor_id)
        if success:
            return {"message": "Senha alterada com sucesso"}
        else:
            raise HTTPException(status_code=500, detail="Erro ao alterar senha")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.delete("/{professor_id}", status_code=204)
async def delete_professor(
    professor_id: int,
    service: ProfessorService = Depends(get_professor_service),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Deleta um professor.
    
    Apenas o próprio professor pode deletar seu perfil.
    """
    try:
        success = await service.delete_professor(professor_id, current_user.professor_id)
        if not success:
            raise HTTPException(status_code=404, detail="Professor não encontrado")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")
