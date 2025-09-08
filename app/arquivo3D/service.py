# arquivo3D/service.py

import logging
from typing import List, Optional
from uuid import uuid4
from fastapi import HTTPException
from aiobotocore.session import get_session

from config import settings
from .repository import Arquivo3DRepository
from .factory import Arquivo3DAbstractFactory
from .schemas import Arquivo3DResponse, Arquivo3DCreate, Arquivo3DUpdate, FileFormat, ConversionRequest, EditRequest
from app.dicom.repository import DICOMRepository

S3_BUCKET_NAME = settings.S3_BUCKET_NAME
AWS_REGION = settings.AWS_REGION

logger = logging.getLogger(__name__)

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
        """Mapeia o modelo do Prisma para o schema de resposta."""
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
        """Baixa vários arquivos DICOM do S3."""
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
        """Faz upload de um arquivo 3D para o S3."""
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

    
    async def converter_dicom_para_3d(self, conversion_request: ConversionRequest, user_id: int) -> Arquivo3DResponse:
        """Converte DICOMs para um arquivo 3D, faz upload e salva metadados."""
        dicom_id = conversion_request.dicom_id
        file_format = conversion_request.file_format

        # 1. Buscar o registro do DICOM
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
            # Configura parâmetros da factory a partir da requisição
            self.generator.set_parameters(
                iso_value=conversion_request.iso_value,
                simplify_target_faces=conversion_request.simplify_target_faces
            )
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
        try:
            novo_arquivo_3d = await self.repository.create(db_data)
            return await self._map_to_response(novo_arquivo_3d)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao salvar metadados no banco de dados: {str(e)}")

    
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
        """Retorna todos os arquivos 3D (opcionalmente filtrados por usuário)."""
        if current_user_id:
            files = await self.repository.find_by_professor_id(current_user_id)
        else:
            files = await self.repository.get_all()

        return [await self._map_to_response(f) for f in files if f]

    async def get_files_by_dicom_id(self, dicom_id: int, current_user_id: int) -> List[Arquivo3DResponse]:
        """Retorna arquivos 3D de um DICOM específico."""
        # Verificar se o DICOM existe e se o usuário tem permissão
        dicom_record = await self.dicom_repository.get_dicom_by_id(dicom_id)
        if not dicom_record:
            raise HTTPException(status_code=404, detail="Registro DICOM não encontrado")

        if dicom_record.professor_id != current_user_id:
            raise HTTPException(status_code=403, detail="Você não tem permissão para acessar estes arquivos")

        files = await self.repository.find_by_dicom_id(dicom_id)
        return [await self._map_to_response(f) for f in files if f]

    async def get_file_by_id(self, arquivo_id: int) -> Optional[Arquivo3DResponse]:
        """Retorna um arquivo 3D pelo ID."""
        arquivo = await self.repository.find_by_id(arquivo_id)
        return await self._map_to_response(arquivo) if arquivo else None

    async def delete_file(self, arquivo_id: int, current_user_id: int) -> bool:
        """Deleta um arquivo 3D e remove do S3."""
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
    
    async def get_volume_dimensions(self, dicom_id: int, user_id: int) -> dict:
        """Retorna as dimensões do volume criado a partir dos DICOMs."""
        dicom_record = await self.dicom_repository.get_dicom_by_id(dicom_id)
        if not dicom_record or dicom_record.professor_id != user_id:
            raise HTTPException(status_code=404, detail="Registro DICOM não encontrado ou sem permissão")

        dicom_urls = dicom_record.s3_urls or []
        if not dicom_urls:
            raise HTTPException(status_code=400, detail="Nenhum arquivo DICOM associado")

        dicom_files_content = await self._download_dicom_files_from_s3(dicom_urls)

        try:
            dims = self.generator.get_volume_dimensions(dicom_files_content)
            return {
                "dicom_id": dicom_id,
                "axial_slices": dims[0],
                "coronal_slices": dims[1],
                "sagittal_slices": dims[2],
                "dimensions": dims
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao calcular dimensões do volume: {e}")


    async def get_slice_image(self, dicom_id: int, user_id: int, plane: str, slice_index: int) -> bytes:
        """Gera imagem PNG de uma fatia específica do volume DICOM."""
        dicom_record = await self.dicom_repository.get_dicom_by_id(dicom_id)
        if not dicom_record or dicom_record.professor_id != user_id:
            raise HTTPException(status_code=404, detail="Registro DICOM não encontrado ou sem permissão")

        dicom_urls = dicom_record.s3_urls or []
        if not dicom_urls:
            raise HTTPException(status_code=400, detail="Nenhum arquivo DICOM associado")

        dicom_files_content = await self._download_dicom_files_from_s3(dicom_urls)

        try:
            image_bytes = self.generator.get_slice_image(dicom_files_content, plane, slice_index)
            return image_bytes
        except (ValueError, IndexError) as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro na geração da imagem da fatia: {e}")
        
    async def edit_3d_file(self, original_arquivo_id: int, user_id: int, edit_params: EditRequest) -> Arquivo3DResponse:
        """Edita um arquivo 3D existente e cria uma nova versão."""
        # 1. Obter metadados do arquivo original para permissão e formato
        original_arquivo = await self.repository.find_by_id(original_arquivo_id)
        if not original_arquivo:
            raise HTTPException(status_code=404, detail="Arquivo 3D original não encontrado.")

        if original_arquivo.DICOM.professor_id != user_id:
            raise HTTPException(status_code=403, detail="Você não tem permissão para editar este arquivo.")

        # 2. Baixar o conteúdo do arquivo 3D original do S3
        original_mesh_content = await self.get_file_content(original_arquivo_id, user_id)

        # 3. Chamar a factory para realizar a edição
        try:
            output_format = edit_params.new_file_format or original_arquivo.file_format

            edited_mesh_content = self.generator.edit_mesh(
                mesh_content=original_mesh_content,
                operation=edit_params.operation.value,
                box_center=list(edit_params.box_center),
                box_size=list(edit_params.box_size),
                output_format=output_format.value
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro durante a edição da malha: {e}")

        # 4. Fazer o upload do novo arquivo editado para o S3
        dicom_id = original_arquivo.dicom_id
        new_object_key = await self._upload_3d_file_to_s3(edited_mesh_content, user_id, dicom_id, output_format)

        # 5. Salvar os metadados do novo arquivo no banco de dados
        db_data = {
            "s3_url": new_object_key,
            "dicom_id": dicom_id,
            "file_format": output_format.value,
            "file_size": len(edited_mesh_content)
        }

        novo_arquivo_editado = await self.repository.create(db_data)
        return await self._map_to_response(novo_arquivo_editado)