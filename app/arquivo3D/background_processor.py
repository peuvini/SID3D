# arquivo3D/background_processor.py

import asyncio
import traceback
from typing import Dict, List
from datetime import datetime
import logging

from .conversion_job_repository import ConversionJobRepository
from .repository import Arquivo3DRepository
from .factory import Arquivo3DFactoryImpl
from .schemas import ConversionStatus
from app.dicom.repository import DICOMRepository
from config import Config


logger = logging.getLogger(__name__)


class BackgroundConversionProcessor:
    """Processador de conversões 3D em background."""

    def __init__(
        self,
        job_repository: ConversionJobRepository,
        arquivo_repository: Arquivo3DRepository,
        dicom_repository: DICOMRepository,
        factory: Arquivo3DFactoryImpl,
        config: Config
    ):
        self.job_repository = job_repository
        self.arquivo_repository = arquivo_repository
        self.dicom_repository = dicom_repository
        self.factory = factory
        self.config = config
        self._running_jobs: Dict[str, asyncio.Task] = {}

    async def start_conversion_job(self, job_id: str) -> bool:
        """Inicia o processamento de um job de conversão."""
        # Verificar se o job já está sendo processado
        if job_id in self._running_jobs:
            logger.warning(f"Job {job_id} já está sendo processado")
            return False

        # Buscar o job
        job = await self.job_repository.get_job_by_id(job_id)
        if not job:
            logger.error(f"Job {job_id} não encontrado")
            return False

        if job["status"] != ConversionStatus.PENDING.value:
            logger.warning(f"Job {job_id} não está no status PENDING (atual: {job['status']})")
            return False

        # Criar e iniciar a task
        task = asyncio.create_task(self._process_conversion_job(job_id))
        self._running_jobs[job_id] = task
        
        logger.info(f"Job {job_id} iniciado para processamento")
        return True

    async def _process_conversion_job(self, job_id: str):
        """Processa uma conversão 3D."""
        try:
            # Atualizar status para PROCESSING
            await self.job_repository.update_job_status(
                job_id, 
                ConversionStatus.PROCESSING.value,
                started_at=datetime.now(),
                progress=0.0,
                message="Iniciando conversão..."
            )

            # Buscar dados do job
            job = await self.job_repository.get_job_by_id(job_id)
            dicom_id = job["dicom_id"]
            file_format = job["file_format"]

            # 1. Buscar o registro do DICOM
            await self.job_repository.update_job_status(
                job_id, 
                ConversionStatus.PROCESSING.value,
                progress=10.0,
                message="Buscando arquivos DICOM..."
            )

            dicom_record = await self.dicom_repository.get_dicom_by_id(dicom_id)
            if not dicom_record:
                raise ValueError("Registro DICOM não encontrado")

            # 2. Extrair URLs dos arquivos DICOM
            dicom_urls = dicom_record.s3_urls or []
            if not dicom_urls:
                raise ValueError("Nenhum arquivo DICOM encontrado para conversão")

            # 3. Baixar os arquivos DICOM do S3
            await self.job_repository.update_job_status(
                job_id, 
                ConversionStatus.PROCESSING.value,
                progress=30.0,
                message="Baixando arquivos DICOM..."
            )

            dicom_files_content = await self._download_dicom_files_from_s3(dicom_urls)
            if not dicom_files_content:
                raise ValueError("Nenhum conteúdo DICOM válido encontrado")

            # 4. Configurar a factory
            await self.job_repository.update_job_status(
                job_id, 
                ConversionStatus.PROCESSING.value,
                progress=40.0,
                message="Configurando parâmetros de conversão..."
            )

            self.factory.set_parameters(
                iso_value=job.get("iso_value"),
                simplify_target_faces=job.get("simplify_target_faces")
            )

            # 5. Gerar o arquivo 3D
            await self.job_repository.update_job_status(
                job_id, 
                ConversionStatus.PROCESSING.value,
                progress=50.0,
                message="Gerando malha 3D..."
            )

            # Executar a conversão em um thread pool para não bloquear o event loop
            loop = asyncio.get_event_loop()
            file_3d_content = await loop.run_in_executor(
                None, 
                lambda: self.factory.generate(dicom_files_content, file_format)
            )

            # 6. Fazer upload do arquivo 3D gerado para o S3
            await self.job_repository.update_job_status(
                job_id, 
                ConversionStatus.PROCESSING.value,
                progress=80.0,
                message="Fazendo upload do arquivo 3D..."
            )

            object_key = await self._upload_3d_file_to_s3(
                file_3d_content, 
                job["professor_id"], 
                dicom_id, 
                file_format
            )

            # 7. Salvar metadados no banco de dados
            await self.job_repository.update_job_status(
                job_id, 
                ConversionStatus.PROCESSING.value,
                progress=90.0,
                message="Salvando metadados..."
            )

            db_data = {
                "s3_url": object_key,
                "dicom_id": dicom_id,
                "file_format": file_format,
                "file_size": len(file_3d_content)
            }

            novo_arquivo_3d = await self.arquivo_repository.create(db_data)

            # 8. Finalizar com sucesso
            await self.job_repository.update_job_status(
                job_id, 
                ConversionStatus.COMPLETED.value,
                progress=100.0,
                message="Conversão concluída com sucesso",
                completed_at=datetime.now(),
                arquivo_3d_id=novo_arquivo_3d.id
            )

            logger.info(f"Job {job_id} concluído com sucesso. Arquivo 3D ID: {novo_arquivo_3d.id}")

        except Exception as e:
            # Registrar erro detalhado
            error_details = traceback.format_exc()
            logger.error(f"Erro no job {job_id}: {str(e)}\n{error_details}")

            await self.job_repository.update_job_status(
                job_id, 
                ConversionStatus.FAILED.value,
                message=f"Erro na conversão: {str(e)}",
                error_details=error_details,
                completed_at=datetime.now()
            )

        finally:
            # Remover da lista de jobs em execução
            if job_id in self._running_jobs:
                del self._running_jobs[job_id]

    async def _download_dicom_files_from_s3(self, dicom_urls: List[str]) -> List[bytes]:
        """Baixa arquivos DICOM do S3."""
        # TODO: Implementar download do S3
        # Por enquanto, simular com dados vazios
        logger.warning("Download do S3 não implementado - usando dados simulados")
        return [b"dummy_dicom_data"] * len(dicom_urls)

    async def _upload_3d_file_to_s3(self, file_content: bytes, user_id: int, dicom_id: int, file_format: str) -> str:
        """Faz upload do arquivo 3D para o S3."""
        # TODO: Implementar upload para S3
        # Por enquanto, simular com uma chave fictícia
        object_key = f"3d_files/user_{user_id}/dicom_{dicom_id}_{int(datetime.now().timestamp())}.{file_format}"
        logger.warning(f"Upload para S3 não implementado - usando chave simulada: {object_key}")
        return object_key

    def get_job_status(self, job_id: str) -> dict:
        """Retorna o status de um job."""
        if job_id in self._running_jobs:
            task = self._running_jobs[job_id]
            return {
                "running": True,
                "done": task.done(),
                "cancelled": task.cancelled()
            }
        return {"running": False, "done": True, "cancelled": False}

    async def cancel_job(self, job_id: str) -> bool:
        """Cancela um job em execução."""
        if job_id in self._running_jobs:
            task = self._running_jobs[job_id]
            task.cancel()
            
            await self.job_repository.update_job_status(
                job_id, 
                ConversionStatus.FAILED.value,
                message="Job cancelado pelo usuário",
                completed_at=datetime.now()
            )
            
            return True
        return False
