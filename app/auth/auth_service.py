import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from prisma import Prisma
from .auth_schemas import LoginRequest, RegisterRequest, TokenResponse, UserResponse, AuthResponse


class AuthService:
    """Serviço de autenticação"""
    
    def __init__(self):
        self.prisma = Prisma()
        from config import settings
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.access_token_expire_minutes = settings.JWT_EXPIRE_MINUTES
    
    async def __aenter__(self):
        await self.prisma.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.prisma.disconnect()
    
    def _hash_password(self, password: str) -> str:
        """Hash da senha usando bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def _verify_password(self, password: str, hashed_password: str) -> bool:
        """Verifica se a senha está correta"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    def _create_access_token(self, data: Dict[str, Any]) -> str:
        """Cria um token JWT"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def _verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verifica e decodifica um token JWT"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.JWTError:
            return None
    
    async def register(self, user_data: RegisterRequest) -> AuthResponse:
        """Registra um novo usuário"""
        # Verifica se o email já existe
        existing_user = await self.prisma.professor.find_unique(
            where={"email": user_data.email}
        )
        
        if existing_user:
            raise ValueError("Email já está em uso")
        
        # Hash da senha
        hashed_password = self._hash_password(user_data.senha)
        
        # Cria o usuário
        new_user = await self.prisma.professor.create(
            data={
                "nome": user_data.nome,
                "email": user_data.email,
                "password": hashed_password
            }
        )
        
        # Cria o token
        token_data = {"sub": str(new_user.id), "email": new_user.email}
        access_token = self._create_access_token(token_data)
        
        # Retorna a resposta
        user_response = UserResponse(
            professor_id=new_user.id,
            nome=new_user.nome,
            email=new_user.email
        )
        
        token_response = TokenResponse(
            access_token=access_token,
            expires_in=self.access_token_expire_minutes * 60
        )
        
        return AuthResponse(user=user_response, token=token_response)
    
    async def login(self, login_data: LoginRequest) -> AuthResponse:
        """Faz login do usuário"""
        # Busca o usuário pelo email
        user = await self.prisma.professor.find_unique(
            where={"email": login_data.email}
        )
        if not user:
            raise ValueError("Email ou senha incorretos")
        
        # Verifica a senha
        if not self._verify_password(login_data.senha, user.password):
            raise ValueError("Email ou senha incorretos")
        
        # Cria o token
        token_data = {"sub": str(user.id), "email": user.email}
        access_token = self._create_access_token(token_data)
        
        # Retorna a resposta
        user_response = UserResponse(
            professor_id=user.id,
            nome=user.nome,
            email=user.email
        )
        
        token_response = TokenResponse(
            access_token=access_token,
            expires_in=self.access_token_expire_minutes * 60
        )
        
        return AuthResponse(user=user_response, token=token_response)
    
    async def get_current_user(self, token: str) -> Optional[UserResponse]:
        """Obtém o usuário atual baseado no token"""
        payload = self._verify_token(token)
        if not payload:
            return None
        
        user_id = int(payload.get("sub"))
        user = await self.prisma.professor.find_unique(
            where={"id": user_id}
        )
        
        if not user:
            return None
        
        return UserResponse(
            professor_id=user.id,
            nome=user.nome,
            email=user.email
        ) 