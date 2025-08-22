import os
from typing import List
from dotenv import load_dotenv


class Settings:
    """Configurações da aplicação"""

    def __init__(self):
        load_dotenv()

        # Banco de dados
        self.DATABASE_URL: str = os.getenv("DATABASE_URL")

        # Segurança
        self.SECRET_KEY: str = os.getenv("SECRET_KEY")
        self.JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM")
        self.JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES"))

        # Servidor
        self.HOST: str = os.getenv("HOST")
        self.PORT: int = int(os.getenv("PORT"))
        self.DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

        # CORS
        self.ALLOWED_ORIGINS: List[str] = [
            origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "*").split(",")
        ]

        # S3
        self.S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME")

        # AWS
        self.AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID")
        self.AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.AWS_REGION: str = os.getenv("AWS_REGION")


# Instância global
settings = Settings()
