# arquivo3D/repository.py

from typing import List, Optional
from prisma import Prisma
from prisma.models import Arquivo3D as Arquivo3DModel

class Arquivo3DRepository:
    def __init__(self, db: Prisma):
        self.db = db

    async def create(self, arquivo_data: dict) -> Arquivo3DModel:
        """Cria um novo registro de Arquivo3D no banco de dados."""
        return await self.db.arquivo3d.create(
            data=arquivo_data,
            include={'DICOM': {'include': {'Professor': True}}}
        )

    async def get_all(self) -> List[Arquivo3DModel]:
        """Retorna todos os registros de Arquivo3D."""
        return await self.db.arquivo3d.find_many(
            include={'DICOM': {'include': {'Professor': True}}}
        )

    async def find_by_id(self, arquivo_id: int) -> Optional[Arquivo3DModel]:
        """Retorna um registro de Arquivo3D específico pelo seu ID."""
        return await self.db.arquivo3d.find_unique(
            where={"id": arquivo_id},
            include={'DICOM': {'include': {'Professor': True}}}
        )

    async def find_by_dicom_id(self, dicom_id: int) -> List[Arquivo3DModel]:
        """Retorna todos os arquivos 3D associados a um DICOM ID."""
        return await self.db.arquivo3d.find_many(
            where={"dicom_id": dicom_id},
            include={'DICOM': {'include': {'Professor': True}}}
        )

    async def find_by_professor_id(self, professor_id: int) -> List[Arquivo3DModel]:
        """Retorna todos os arquivos 3D de um professor específico."""
        return await self.db.arquivo3d.find_many(
            where={
                "DICOM": {
                    "professor_id": professor_id
                }
            },
            include={'DICOM': {'include': {'Professor': True}}}
        )

    async def get_latest_version_by_dicom(self, dicom_id: int) -> Optional[Arquivo3DModel]:
        """Retorna a versão mais recente de um arquivo 3D para um DICOM específico."""
        return await self.db.arquivo3d.find_first(
            where={"dicom_id": dicom_id},
            include={'DICOM': {'include': {'Professor': True}}},
            order={'created_at': 'desc'}
        )
    
    async def update(self, arquivo_id: int, update_data: dict) -> Optional[Arquivo3DModel]:
        """Atualiza um registro de Arquivo3D existente."""
        return await self.db.arquivo3d.update(
            where={"id": arquivo_id},
            data=update_data,
            include={'DICOM': {'include': {'Professor': True}}}
        )

    async def delete(self, arquivo_id: int) -> Optional[Arquivo3DModel]:
        """Deleta um registro de Arquivo3D do banco de dados."""
        return await self.db.arquivo3d.delete(where={"id": arquivo_id})

    async def count_by_dicom_id(self, dicom_id: int) -> int:
        """Conta quantos arquivos 3D existem para um DICOM específico."""
        return await self.db.arquivo3d.count(where={"dicom_id": dicom_id})