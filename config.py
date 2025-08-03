import os
from typing import Optional


class Settings:
    """Configurações da aplicação"""
    
    # Banco de dados
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://usuario:senha@localhost:5432/sid3d")
    
    # Segurança
    SECRET_KEY: str = os.getenv("SECRET_KEY", "sua_chave_secreta_muito_segura_aqui_altere_em_producao")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))
    
    # Servidor
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # CORS
    ALLOWED_ORIGINS: list = os.getenv("ALLOWED_ORIGINS", "*").split(",")


# Instância global das configurações
settings = Settings() 