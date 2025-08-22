import os
from aiobotocore.session import get_session
import boto3
from typing import List, Optional
from uuid import uuid4
from fastapi import UploadFile, HTTPException
from config import settings

from .repository import DICOMRepository
from .schemas import DICOMCreate, DICOMResponse, DICOMSearch
from app.utils.mesh_generator import MeshGeneratorAbstract 

s3 = boto3.resource('s3')

S3_BUCKET_NAME = settings.S3_BUCKET_NAME
AWS_REGION = settings.AWS_REGION

class DICOMService:
    def __init__(self, repository: DICOMRepository, mesh_generator: MeshGeneratorAbstract):
        self.repository = repository
        self.mesh_generator = mesh_generator
        self.session = get_session()


    async def _get_s3_client(self):
        return self.session.create_client('s3', region_name=AWS_REGION)

    async def _map_to_response(self, dicom_model) -> DICOMResponse:
        """Helper para mapear o modelo do Prisma para o schema de resposta."""
        if not dicom_model:
            return None
        return DICOMResponse(
            # O modelo Prisma usa DICOM_ID
            dicom_id=dicom_model.DICOM_ID,
            nome=dicom_model.Nome,
            paciente=dicom_model.Paciente,
            url=dicom_model.URL,
            professor_id=dicom_model.ID_Professor,
        )

    async def create_dicom_upload(self, paciente: str , file: list[UploadFile], dicom_data: DICOMCreate, user_id: int) -> DICOMResponse:
        """
        Faz upload de múltiplos arquivos DICOM para o AWS S3 e salva os metadados do primeiro no banco.
        """
        object_keys = []
        try:
            for f in file:
                file_extension = f.filename.split('.')[-1] if '.' in f.filename else 'dcm'
                object_key = f"dicom-files/{user_id}/{paciente}/{uuid4()}.{file_extension}"
                await f.seek(0)  # Reset do ponteiro do arquivo
                content = await f.read()
                print(f"S3_BUCKET_NAME: {S3_BUCKET_NAME}, object_key: {object_key}, content_type: {f.content_type}")
                s3.Object(S3_BUCKET_NAME, object_key).put(
                    Body=content, 
                    ContentType=f.content_type
                )
                object_keys.append(object_key)
        except Exception as e:
            raise IOError(f"Falha no upload para o S3: {e}")

        # Salva o primeiro arquivo no banco
        db_data = {
            "Nome": dicom_data.nome,
            "Paciente": dicom_data.paciente,
            "URL": object_keys[0] if object_keys else None,
            "Professor": {
                "connect": {
                    "Professor_ID": user_id
                }
            }
        }
        
        new_dicom = await self.repository.create_dicom(db_data)
        return await self._map_to_response(new_dicom)

    async def get_dicom_download_url(self, dicom_id: int) -> Optional[str]:
        dicom_record = await self.repository.get_dicom_by_id(dicom_id)
        if not dicom_record:
            return None
        object_key = dicom_record.URL
        try:
            async with await self._get_s3_client() as s3_client:
                download_url = await s3_client.generate_presigned_url(
                    'get_object', Params={'Bucket': S3_BUCKET_NAME, 'Key': object_key}, ExpiresIn=3600
                )
                return download_url
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Não foi possível gerar a URL de download: {e}")

    async def delete_dicom_by_id(self, dicom_id: int, current_user_professor_id: int) -> bool:
        dicom_to_delete = await self.repository.get_dicom_by_id(dicom_id)
        if not dicom_to_delete:
            return False
        if dicom_to_delete.ID_Professor != current_user_professor_id:
            raise PermissionError("Você не tem permissão para deletar este arquivo.")
        object_key = dicom_to_delete.URL
        try:
            async with await self._get_s3_client() as s3_client:
                await s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=object_key)
        except Exception as e:
            print(f"Alerta: Falha ao deletar o objeto {object_key} do S3. Erro: {e}")
        deleted_record = await self.repository.delete_dicom(dicom_id)
        return deleted_record is not None

    async def get_all_dicoms(self) -> List[DICOMResponse]:
        dicoms = await self.repository.get_all_dicoms()
        return [await self._map_to_response(d) for d in dicoms]

    async def search_dicoms(self, search_params: DICOMSearch) -> List[DICOMResponse]:
        search_criteria = {
            "Nome": search_params.nome,
            "Paciente": search_params.paciente
        }
        dicoms = await self.repository.find_dicoms(search_criteria)
        return [await self._map_to_response(d) for d in dicoms]