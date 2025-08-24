# app/impressora/repository.py

from typing import List, Optional
from prisma import Prisma
from prisma.models import Impressora as ImpressoraModel, Impressao3D as Impressao3DModel

class ImpressoraRepository:
    def __init__(self, db: Prisma):
        self.db = db

    async def create_impressora(self, data: dict) -> ImpressoraModel:
        """Cria uma nova impressora no banco de dados."""
        return await self.db.impressora.create(data=data)

    async def get_by_id(self, impressora_id: int) -> Optional[ImpressoraModel]:
        """Busca uma impressora pelo ID."""
        return await self.db.impressora.find_unique(where={"id": impressora_id})

    async def get_all(self) -> List[ImpressoraModel]:
        """Retorna todas as impressoras cadastradas."""
        return await self.db.impressora.find_many()

    async def update(self, impressora_id: int, data: dict) -> Optional[ImpressoraModel]:
        """Atualiza uma impressora existente."""
        return await self.db.impressora.update(where={"id": impressora_id}, data=data)

    async def delete(self, impressora_id: int) -> Optional[ImpressoraModel]:
        """Deleta uma impressora do banco de dados."""
        return await self.db.impressora.delete(where={"id": impressora_id})

class Impressao3DRepository:
    def __init__(self, db: Prisma):
        self.db = db

    async def create_impressao(self, data: dict) -> Impressao3DModel:
        """Cria um novo registro de trabalho de impressão."""
        return await self.db.impressao3d.create(
            data=data,
            include={'Arquivo3D': {'include': {'DICOM': True}}, 'Impressora': True}
        )

    async def get_by_id(self, impressao_id: int) -> Optional[Impressao3DModel]:
        """Busca um trabalho de impressão pelo ID."""
        return await self.db.impressao3d.find_unique(
            where={"id": impressao_id},
            include={'Arquivo3D': {'include': {'DICOM': True}}, 'Impressora': True}
        )

    async def get_all(self) -> List[Impressao3DModel]:
        """Retorna todos os trabalhos de impressão."""
        return await self.db.impressao3d.find_many(
            include={'Arquivo3D': {'include': {'DICOM': True}}, 'Impressora': True}
        )

    async def update_status(self, impressao_id: int, data: dict) -> Impressao3DModel:
        """Atualiza o status e data de conclusão de um trabalho de impressão."""
        return await self.db.impressao3d.update(
            where={"id": impressao_id}, 
            data=data,
            include={'Arquivo3D': {'include': {'DICOM': True}}, 'Impressora': True}
        )