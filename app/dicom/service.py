import os
from aiobotocore.session import get_session
from typing import List, Optional
from uuid import uuid4
from fastapi import UploadFile, HTTPException
from config import settings

from .repository import DICOMRepository
from .schemas import DICOMCreate, DICOMResponse, DICOMSearch, DICOMUpdate

S3_BUCKET_NAME = settings.S3_BUCKET_NAME
AWS_REGION = settings.AWS_REGION

class DICOMService:
    def __init__(self, repository: DICOMRepository):
        self.repository = repository
        self.session = get_session()

    async def _get_s3_client(self):
        """Cria e retorna um cliente S3 assíncrono."""
        return self.session.create_client('s3', region_name=AWS_REGION)

    async def _map_to_response(self, dicom_model) -> DICOMResponse:
        """Helper para mapear o modelo do Prisma para o schema de resposta."""
        if not dicom_model:
            return None
        
        return DICOMResponse(
            id=dicom_model.id,
            nome=dicom_model.nome,
            paciente=dicom_model.paciente,
            professor_id=dicom_model.professor_id,
            s3_urls=dicom_model.s3_urls or [],
            created_at=dicom_model.created_at,
            updated_at=dicom_model.updated_at
        )

    async def create_dicom_upload(self, files: List[UploadFile], dicom_data: DICOMCreate, user_id: int) -> DICOMResponse:
        """
        Faz upload de múltiplos arquivos DICOM para o AWS S3 e salva os metadados no banco.
        
        Args:
            files: Lista de arquivos para upload
            dicom_data: Dados do exame (nome e paciente)
            user_id: ID do professor responsável
            
        Returns:
            DICOMResponse com os dados salvos
        """
        # Validações
        if not files:
            raise HTTPException(status_code=400, detail="Pelo menos um arquivo deve ser enviado")

        uploaded_urls = []
        try:
            async with await self._get_s3_client() as s3_client:
                for i, file in enumerate(files):
                    if not file.filename:
                        continue
                    file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'dcm'
                    object_key = f"dicom-files/{user_id}/{uuid4()}.{file_extension}"
                    await file.seek(0)
                    content = await file.read()
                    if not content:
                        continue
                    await s3_client.put_object(
                        Bucket=S3_BUCKET_NAME,
                        Key=object_key,
                        Body=content,
                        ContentType=file.content_type or 'application/octet-stream'
                    )
                    uploaded_urls.append(object_key)
        except Exception as e:
            # Se falhar, tenta limpar os arquivos já enviados
            try:
                await self._cleanup_s3_files(uploaded_urls)
            except:
                pass
            raise HTTPException(status_code=500, detail=f"Falha no upload para o S3: {str(e)}")

        if not uploaded_urls:
            raise HTTPException(status_code=400, detail="Nenhum arquivo válido foi processado")

        # Cria registro DICOM no banco apenas se o upload foi bem-sucedido
        db_data = {
            "nome": dicom_data.nome,
            "paciente": dicom_data.paciente,
            "professor_id": user_id,
            "s3_urls": uploaded_urls
        }
        new_dicom = await self.repository.create_dicom(db_data)
        return await self._map_to_response(new_dicom)

    async def _cleanup_s3_files(self, object_keys: List[str]) -> None:
        """Remove arquivos do S3 em caso de erro."""
        if not object_keys:
            return
            
        try:
            async with await self._get_s3_client() as s3_client:
                for object_key in object_keys:
                    await s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=object_key)
        except Exception as e:
            print(f"Erro ao limpar arquivos do S3: {e}")

    async def get_dicom_download_url(self, dicom_id: int, file_index: int = 0) -> Optional[str]:
        """
        Gera URL pré-assinada para download de um arquivo DICOM específico.
        
        Args:
            dicom_id: ID do registro DICOM
            file_index: Índice do arquivo na lista (default: 0 para o primeiro)
            
        Returns:
            URL pré-assinada ou None se não encontrado
        """
        dicom_record = await self.repository.get_dicom_by_id(dicom_id)
        if not dicom_record:
            return None
            
        urls = dicom_record.s3_urls or []
        if not urls or file_index >= len(urls):
            return None
            
        object_key = urls[file_index]
        
        try:
            async with await self._get_s3_client() as s3_client:
                download_url = await s3_client.generate_presigned_url(
                    'get_object', 
                    Params={'Bucket': S3_BUCKET_NAME, 'Key': object_key}, 
                    ExpiresIn=3600
                )
                return download_url
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Não foi possível gerar a URL de download: {e}")

    async def update_dicom(self, dicom_id: int, update_data: DICOMUpdate, current_user_id: int) -> Optional[DICOMResponse]:
        """
        Atualiza os metadados de um registro DICOM.
        
        Args:
            dicom_id: ID do registro DICOM
            update_data: Dados para atualização
            current_user_id: ID do usuário atual (para verificação de permissão)
            
        Returns:
            DICOMResponse atualizado ou None se não encontrado
        """
        # Verifica se o registro existe e se o usuário tem permissão
        existing_dicom = await self.repository.get_dicom_by_id(dicom_id)
        if not existing_dicom:
            return None
            
        if existing_dicom.professor_id != current_user_id:
            raise HTTPException(status_code=403, detail="Você não tem permissão para editar este registro")

        # Prepara dados para atualização (apenas campos não-nulos)
        update_dict = {}
        if update_data.nome is not None:
            update_dict["nome"] = update_data.nome
        if update_data.paciente is not None:
            update_dict["paciente"] = update_data.paciente

        if not update_dict:
            return await self._map_to_response(existing_dicom)

        updated_dicom = await self.repository.update_dicom(dicom_id, update_dict)
        return await self._map_to_response(updated_dicom)
    
    async def delete_dicom_by_id(self, dicom_id: int, current_user_professor_id: int) -> bool:
        """
        Deleta um registro DICOM e seus arquivos associados do S3.
        
        Args:
            dicom_id: ID do registro DICOM
            current_user_professor_id: ID do professor atual (para verificação de permissão)
            
        Returns:
            True se deletado com sucesso, False se não encontrado
        """
        dicom_to_delete = await self.repository.get_dicom_by_id(dicom_id)
        if not dicom_to_delete:
            return False
            
        if dicom_to_delete.professor_id != current_user_professor_id:
            raise HTTPException(status_code=403, detail="Você não tem permissão para deletar este arquivo")

        # Remove arquivos do S3
        urls = dicom_to_delete.s3_urls or []
        if urls:
            try:
                await self._cleanup_s3_files(urls)
            except Exception as e:
                print(f"Alerta: Falha ao deletar arquivos do S3: {e}")

        # Remove registro do banco
        deleted_record = await self.repository.delete_dicom(dicom_id)
        return deleted_record is not None

    async def get_dicoms_by_professor_id(self, current_user_id: Optional[int] = None) -> List[DICOMResponse]:
        """
        Retorna todos os registros DICOM.
        
        Args:
            current_user_id: Se fornecido, filtra apenas os DICOMs do usuário
        
        Returns:
            Lista de DICOMResponse
        """
        if current_user_id:
            dicoms = await self.repository.get_dicoms_by_professor(current_user_id)
        else:
            dicoms = await self.repository.get_all_dicoms()
            
        return [await self._map_to_response(d) for d in dicoms if d]

    async def search_dicoms(self, search_params: DICOMSearch, current_user_id: Optional[int] = None) -> List[DICOMResponse]:
        """
        Busca registros DICOM com base nos parâmetros fornecidos.
        
        Args:
            search_params: Parâmetros de busca (nome, paciente)
            current_user_id: Se fornecido, filtra apenas os DICOMs do usuário
            
        Returns:
            Lista de DICOMResponse que atendem aos critérios
        """
        search_criteria = {}
        
        if search_params.nome:
            search_criteria["nome"] = search_params.nome
        if search_params.paciente:
            search_criteria["paciente"] = search_params.paciente
            
        # Se especificado um usuário, adiciona aos critérios
        if current_user_id:
            search_criteria["professor_id"] = current_user_id
            
        dicoms = await self.repository.find_dicoms(search_criteria)
        return [await self._map_to_response(d) for d in dicoms if d]

    async def get_dicom_by_id(self, dicom_id: int) -> Optional[DICOMResponse]:
        """
        Retorna um registro DICOM específico pelo ID.
        
        Args:
            dicom_id: ID do registro DICOM
            
        Returns:
            DICOMResponse ou None se não encontrado
        """
        dicom = await self.repository.get_dicom_by_id(dicom_id)
        return await self._map_to_response(dicom) if dicom else None