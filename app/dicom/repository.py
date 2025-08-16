# app/dicom/repository.py

from typing import List, Optional
from prisma import Prisma
from prisma.models import Dicom as DicomModel # Supondo que o modelo Prisma se chame 'Dicom'

class DICOMRepository:
    def __init__(self, db: Prisma):
        self.db = db

    async def create_dicom(self, dicom_data: dict) -> DicomModel:
        """Cria um novo registro DICOM no banco de dados."""
        return await self.db.dicom.create(data=dicom_data)

    async def get_all_dicoms(self) -> List[DicomModel]:
        """Retorna todos os registros DICOM."""
        return await self.db.dicom.find_many()

    async def get_dicom_by_id(self, dicom_id: int) -> Optional[DicomModel]:
        """Retorna um registro DICOM específico pelo seu ID."""
        return await self.db.dicom.find_unique(where={"DICOM_ID": dicom_id}) # Adeque 'DICOM_ID' ao seu schema.prisma

    async def find_dicoms(self, search_criteria: dict) -> List[DicomModel]:
        """Encontra registros DICOM com base em um critério de busca."""
        # Remove chaves com valor None para não filtrar por elas
        where_clause = {k: v for k, v in search_criteria.items() if v is not None}
        return await self.db.dicom.find_many(where=where_clause)

    async def update_dicom(self, dicom_id: int, update_data: dict) -> Optional[DicomModel]:
        """Atualiza um registro DICOM existente."""
        return await self.db.dicom.update(
            where={"DICOM_ID": dicom_id},
            data=update_data
        )

    async def delete_dicom(self, dicom_id: int) -> Optional[DicomModel]:
        """Deleta um registro DICOM do banco de dados."""
        return await self.db.dicom.delete(where={"DICOM_ID": dicom_id})