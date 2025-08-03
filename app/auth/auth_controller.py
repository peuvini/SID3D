from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .auth_service import AuthService
from .auth_schemas import LoginRequest, RegisterRequest, AuthResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["Autenticação"])
security = HTTPBearer()


@router.post("/register", response_model=AuthResponse)
async def register(user_data: RegisterRequest):
    """Registra um novo usuário"""
    try:
        async with AuthService() as auth_service:
            result = await auth_service.register(user_data)
            return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.post("/login", response_model=AuthResponse)
async def login(login_data: LoginRequest):
    """Faz login do usuário"""
    try:
        async with AuthService() as auth_service:
            result = await auth_service.login(login_data)
            return result
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.get("/me", response_model=UserResponse)
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Obtém informações do usuário atual"""
    try:
        async with AuthService() as auth_service:
            user = await auth_service.get_current_user(credentials.credentials)
            if not user:
                raise HTTPException(status_code=401, detail="Token inválido ou expirado")
            return user
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro interno do servidor") 