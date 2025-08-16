# app/impressora/repository.py

from typing import List, Optional
from prisma import Prisma
from prisma.models import Impressora as ImpressoraModel, Impressao as ImpressaoModel

class ImpressoraRepository:
    def __init__(self, db: Prisma):
        self.db = db

    async def create_impressora(self, data: dict) -> ImpressoraModel:
        """Cria uma nova impressora no banco de dados."""
        return await self.db.impressora.create(data=data)

    async def get_by_id(self, impressora_id: int) -> Optional[ImpressoraModel]:
        """Busca uma impressora pelo ID."""
        return await self.db.impressora.find_unique(where={"id": impressora_id})

    async def get_by_ip(self, ip: str) -> Optional[ImpressoraModel]:
        """Busca uma impressora pelo endereço IP."""
        return await self.db.impressora.find_unique(where={"ip": ip})

    async def get_all(self) -> List[ImpressoraModel]:
        """Retorna todas as impressoras cadastradas."""
        return await self.db.impressora.find_many()

class ImpressaoRepository:
    def __init__(self, db: Prisma):
        self.db = db

    async def create_impressao(self, data: dict) -> ImpressaoModel:
        """Cria um novo registro de trabalho de impressão (log)."""
        return await self.db.impressao.create(data=data)

    async def get_by_id(self, impressao_id: int) -> Optional[ImpressaoModel]:
        """Busca um trabalho de impressão pelo ID."""
        return await self.db.impressao.find_unique(where={"id": impressao_id})

    async def update_status(self, impressao_id: int, data: dict) -> ImpressaoModel:
        """Atualiza o status e data de conclusão de um trabalho de impressão."""
        return await self.db.impressao.update(where={"id": impressao_id}, data=data)