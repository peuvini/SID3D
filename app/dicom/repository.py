from typing import List, Optional
from prisma import Prisma
from prisma.models import DICOM as DicomModel

class DICOMRepository:
    def __init__(self, db: Prisma):
        self.db = db

    async def create_dicom(self, dicom_data: dict) -> DicomModel:
        """Cria um novo registro DICOM no banco de dados."""
        return await self.db.dicom.create(data=dicom_data)

    async def get_all_dicoms(self) -> List[DicomModel]:
        """Retorna todos os registros DICOM."""
        return await self.db.dicom.find_many(
            include={'Professor': True, 'Arquivo3D': True}
        )

    async def get_dicom_by_id(self, dicom_id: int) -> Optional[DicomModel]:
        """Retorna um registro DICOM específico pelo seu ID."""
        return await self.db.dicom.find_unique(
            where={"id": dicom_id},
            include={'Professor': True, 'Arquivo3D': True}
        )

    async def get_dicoms_by_professor(self, professor_id: int) -> List[DicomModel]:
        """Retorna todos os DICOMs de um professor específico."""
        return await self.db.dicom.find_many(
            where={"professor_id": professor_id},
            include={'Professor': True, 'Arquivo3D': True}
        )

    async def find_dicoms(self, search_criteria: dict) -> List[DicomModel]:
        """Encontra registros DICOM com base em critérios de busca."""
        where_clause = {}
        
        # Adiciona filtros de busca por nome e paciente (case-insensitive)
        if search_criteria.get('nome'):
            where_clause['nome'] = {
                'contains': search_criteria['nome'],
                'mode': 'insensitive'
            }
        
        if search_criteria.get('paciente'):
            where_clause['paciente'] = {
                'contains': search_criteria['paciente'],
                'mode': 'insensitive'
            }
        
        return await self.db.dicom.find_many(
            where=where_clause,
            include={'Professor': True, 'Arquivo3D': True}
        )
    
    async def update_dicom(self, dicom_id: int, update_data: dict) -> Optional[DicomModel]:
        """Atualiza um registro DICOM existente."""
        return await self.db.dicom.update(
            where={"id": dicom_id},
            data=update_data,
            include={'Professor': True, 'Arquivo3D': True}
        )

    async def update_dicom_urls(self, dicom_id: int, urls: List[str]) -> Optional[DicomModel]:
        """Atualiza apenas as URLs de um registro DICOM."""
        return await self.update_dicom(dicom_id, {"s3_urls": urls})

    async def delete_dicom(self, dicom_id: int) -> Optional[DicomModel]:
        """Deleta um registro DICOM do banco de dados."""
        return await self.db.dicom.delete(where={"id": dicom_id})