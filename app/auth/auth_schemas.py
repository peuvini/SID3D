from pydantic import BaseModel, EmailStr
from typing import Optional


class LoginRequest(BaseModel):
    """Schema para requisição de login"""
    email: EmailStr
    senha: str


class RegisterRequest(BaseModel):
    """Schema para requisição de registro"""
    nome: str
    email: EmailStr
    senha: str


class TokenResponse(BaseModel):
    """Schema para resposta de token"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    """Schema para resposta de usuário"""
    professor_id: int
    nome: str
    email: str


class AuthResponse(BaseModel):
    """Schema para resposta de autenticação"""
    user: UserResponse
    token: TokenResponse 