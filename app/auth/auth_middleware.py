from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .auth_service import AuthService
from .auth_schemas import UserResponse

security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserResponse:
    """Middleware para obter o usuário atual e verificar autenticação"""
    try:
        async with AuthService() as auth_service:
            user = await auth_service.get_current_user(credentials.credentials)
            if not user:
                raise HTTPException(
                    status_code=401,
                    detail="Token inválido ou expirado",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


def require_auth():
    """Decorator para rotas que requerem autenticação"""
    return Depends(get_current_user) 