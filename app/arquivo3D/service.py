# arquivo3D/service.py

from typing import List, Optional
from uuid import uuid4
from fastapi import HTTPException
from aiobotocore.session import get_session

from config import settings
from .repository import Arquivo3DRepository
from .factory import Arquivo3DAbstractFactory
from .schemas import Arquivo3DResponse, Arquivo3DCreate, Arquivo3DUpdate, FileFormat
from app.dicom.repository import DICOMRepository

S3_BUCKET_NAME = settings.S3_BUCKET_NAME
AWS_REGION = settings.AWS_REGION

class Arquivo3DService:
    def __init__(self, repository: Arquivo3DRepository, dicom_repository: DICOMRepository, generator: Arquivo3DAbstractFactory):
        self.repository = repository
        self.dicom_repository = dicom_repository
        self.generator = generator
        self.session = get_session()

    async def _get_s3_client(self):
        """Cria e retorna um cliente S3 assíncrono."""
        return self.session.create_client('s3', region_name=AWS_REGION)

    async def _map_to_response(self, model) -> Arquivo3DResponse:
        """Helper para mapear o modelo do Prisma para o schema de resposta."""
        if not model:
            return None
        
        return Arquivo3DResponse(
            id=model.id,
            dicom_id=model.dicom_id,
            s3_url=model.s3_url,
            file_format=FileFormat(model.file_format),
            file_size=model.file_size,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    async def _download_dicom_files_from_s3(self, dicom_urls: List[str]) -> List[bytes]:
        """Baixa múltiplos arquivos DICOM do S3."""
        dicom_files_content = []
        
        try:
            async with await self._get_s3_client() as s3_client:
                for url in dicom_urls:
                    response = await s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=url)
                    content = await response['Body'].read()
                    dicom_files_content.append(content)
                    
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao baixar arquivos DICOM do S3: {str(e)}")
            
        return dicom_files_content

    async def _upload_3d_file_to_s3(self, file_content: bytes, user_id: int, dicom_id: int, file_format: FileFormat) -> str:
        """Faz upload do arquivo 3D para o S3."""
        object_key = f"3d-files/{user_id}/{dicom_id}/{uuid4()}.{file_format.value}"
        
        content_types = {
            FileFormat.STL: 'model/stl',
            FileFormat.OBJ: 'model/obj',
            FileFormat.PLY: 'model/ply'
        }
        
        try:
            async with await self._get_s3_client() as s3_client:
                await s3_client.put_object(
                    Bucket=S3_BUCKET_NAME,
                    Key=object_key,
                    Body=file_content,
                    ContentType=content_types.get(file_format, 'application/octet-stream')
                )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao fazer upload do arquivo {file_format.value.upper()} para o S3: {str(e)}")
            
        return object_key

    async def converter_dicom_para_3d(self, dicom_id: int, user_id: int, file_format: FileFormat = FileFormat.STL) -> Arquivo3DResponse:
        """
        Converte uma série de arquivos DICOM em um arquivo 3D, faz o upload
        para o S3 e salva os metadados no banco.
        
        Args:
            dicom_id: ID do registro DICOM
            user_id: ID do professor responsável
            file_format: Formato desejado para o arquivo 3D
            
        Returns:
            Arquivo3DResponse com os dados do arquivo criado
        """
        # 1. Buscar o registro do DICOM para obter as URLs dos arquivos
        dicom_record = await self.dicom_repository.get_dicom_by_id(dicom_id)
        if not dicom_record:
            raise HTTPException(status_code=404, detail="Registro DICOM não encontrado")
            
        # Verificar se o usuário tem permissão (é o dono do DICOM)
        if dicom_record.professor_id != user_id:
            raise HTTPException(status_code=403, detail="Você não tem permissão para converter este DICOM")

        # 2. Extrair URLs dos arquivos DICOM do campo s3_urls
        dicom_urls = dicom_record.s3_urls or []
        if not dicom_urls:
            raise HTTPException(status_code=400, detail="Nenhum arquivo DICOM encontrado para conversão")

        # 3. Baixar os arquivos DICOM do S3
        dicom_files_content = await self._download_dicom_files_from_s3(dicom_urls)
        
        if not dicom_files_content:
            raise HTTPException(status_code=400, detail="Nenhum conteúdo DICOM válido encontrado")

        # 4. Gerar o arquivo 3D usando a factory
        try:
            file_3d_content = self.generator.generate(dicom_files_content, file_format.value)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro na geração do arquivo 3D: {str(e)}")

        # 5. Fazer upload do arquivo 3D gerado para o S3
        object_key = await self._upload_3d_file_to_s3(file_3d_content, user_id, dicom_id, file_format)

        # 6. Salvar metadados no banco de dados
        db_data = {
            "s3_url": object_key,
            "dicom_id": dicom_id,
            "file_format": file_format.value,
            "file_size": len(file_3d_content)
        }
        
        novo_arquivo_3d = await self.repository.create(db_data)
        return await self._map_to_response(novo_arquivo_3d)

    async def get_download_url(self, arquivo_id: int, current_user_id: int) -> Optional[str]:
        """
        Gera URL pré-assinada para download de um arquivo 3D.
        
        Args:
            arquivo_id: ID do arquivo 3D
            current_user_id: ID do usuário atual (para verificação de permissão)
            
        Returns:
            URL pré-assinada ou None se não encontrado
        """
        arquivo_record = await self.repository.find_by_id(arquivo_id)
        if not arquivo_record:
            return None
            
        # Verificar permissão através do relacionamento DICOM->Professor
        if hasattr(arquivo_record, 'DICOM') and arquivo_record.DICOM:
            if arquivo_record.DICOM.professor_id != current_user_id:
                raise HTTPException(status_code=403, detail="Você não tem permissão para acessar este arquivo")

        try:
            async with await self._get_s3_client() as s3_client:
                download_url = await s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': S3_BUCKET_NAME, 'Key': arquivo_record.s3_url},
                    ExpiresIn=3600
                )
                return download_url
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Não foi possível gerar a URL de download: {str(e)}")

    async def get_file_content(self, arquivo_id: int, current_user_id: int) -> bytes:
        """
        Busca um arquivo 3D no S3 e retorna seu conteúdo em bytes.
        
        Args:
            arquivo_id: ID do arquivo 3D
            current_user_id: ID do usuário atual (para verificação de permissão)
            
        Returns:
            Conteúdo do arquivo em bytes
        """
        arquivo_record = await self.repository.find_by_id(arquivo_id)
        if not arquivo_record:
            raise HTTPException(status_code=404, detail="Arquivo 3D não encontrado")
            
        # Verificar permissão através do relacionamento DICOM->Professor
        if hasattr(arquivo_record, 'DICOM') and arquivo_record.DICOM:
            if arquivo_record.DICOM.professor_id != current_user_id:
                raise HTTPException(status_code=403, detail="Você não tem permissão para acessar este arquivo")

        try:
            async with await self._get_s3_client() as s3_client:
                response = await s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=arquivo_record.s3_url)
                return await response['Body'].read()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao obter arquivo do S3: {str(e)}")

    async def get_all_files(self, current_user_id: Optional[int] = None) -> List[Arquivo3DResponse]:
        """
        Retorna todos os arquivos 3D.
        
        Args:
            current_user_id: Se fornecido, filtra apenas os arquivos do usuário
        
        Returns:
            Lista de Arquivo3DResponse
        """
        if current_user_id:
            files = await self.repository.find_by_professor_id(current_user_id)
        else:
            files = await self.repository.get_all()
        
        return [await self._map_to_response(f) for f in files if f]

    async def get_files_by_dicom_id(self, dicom_id: int, current_user_id: int) -> List[Arquivo3DResponse]:
        """
        Retorna todos os arquivos 3D associados a um DICOM específico.
        
        Args:
            dicom_id: ID do registro DICOM
            current_user_id: ID do usuário atual (para verificação de permissão)
            
        Returns:
            Lista de Arquivo3DResponse
        """
        # Verificar se o DICOM existe e se o usuário tem permissão
        dicom_record = await self.dicom_repository.get_dicom_by_id(dicom_id)
        if not dicom_record:
            raise HTTPException(status_code=404, detail="Registro DICOM não encontrado")
            
        if dicom_record.professor_id != current_user_id:
            raise HTTPException(status_code=403, detail="Você não tem permissão para acessar estes arquivos")

        files = await self.repository.find_by_dicom_id(dicom_id)
        return [await self._map_to_response(f) for f in files if f]

    async def get_file_by_id(self, arquivo_id: int) -> Optional[Arquivo3DResponse]:
        """
        Retorna um arquivo 3D específico pelo ID.
        
        Args:
            arquivo_id: ID do arquivo 3D
            
        Returns:
            Arquivo3DResponse ou None se não encontrado
        """
        arquivo = await self.repository.find_by_id(arquivo_id)
        return await self._map_to_response(arquivo) if arquivo else None

    async def delete_file(self, arquivo_id: int, current_user_id: int) -> bool:
        """
        Deleta um arquivo 3D e remove do S3.
        
        Args:
            arquivo_id: ID do arquivo 3D
            current_user_id: ID do usuário atual (para verificação de permissão)
            
        Returns:
            True se deletado com sucesso, False se não encontrado
        """
        arquivo_record = await self.repository.find_by_id(arquivo_id)
        if not arquivo_record:
            return False
            
        # Verificar permissão através do relacionamento DICOM->Professor
        if hasattr(arquivo_record, 'DICOM') and arquivo_record.DICOM:
            if arquivo_record.DICOM.professor_id != current_user_id:
                raise HTTPException(status_code=403, detail="Você não tem permissão para deletar este arquivo")

        # Remove arquivo do S3
        try:
            async with await self._get_s3_client() as s3_client:
                await s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=arquivo_record.s3_url)
        except Exception as e:
            print(f"Alerta: Falha ao deletar arquivo do S3: {e}")

        # Remove registro do banco
        deleted_record = await self.repository.delete(arquivo_id)
        return deleted_record is not None