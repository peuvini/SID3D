# arquivo3D/conversion_job_repository.py

from datetime import datetime
from typing import List, Optional
from prisma import Prisma
from .schemas import ConversionStatus


class ConversionJobRepository:
    """Repository para gerenciar jobs de conversão DICOM para 3D."""

    def __init__(self, db: Prisma):
        self.db = db

    async def create_job(self, data: dict) -> dict:
        """Cria um novo job de conversão."""
        # Por enquanto, simularemos com um dicionário em memória
        # até que a migração seja aplicada
        job_id = f"job_{data['dicom_id']}_{int(datetime.now().timestamp())}"
        
        job_data = {
            "id": job_id,
            "dicom_id": data["dicom_id"],
            "professor_id": data["professor_id"],
            "file_format": data["file_format"],
            "status": ConversionStatus.PENDING.value,
            "iso_value": data.get("iso_value"),
            "simplify_target_faces": data.get("simplify_target_faces"),
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "progress": None,
            "message": None,
            "error_details": None,
            "arquivo_3d_id": None,
            "started_at": None,
            "completed_at": None
        }
        
        # Armazenar temporariamente em uma variável de classe
        if not hasattr(ConversionJobRepository, '_jobs'):
            ConversionJobRepository._jobs = {}
        
        ConversionJobRepository._jobs[job_id] = job_data
        return job_data

    async def get_job_by_id(self, job_id: str) -> Optional[dict]:
        """Busca um job pelo ID."""
        if hasattr(ConversionJobRepository, '_jobs'):
            return ConversionJobRepository._jobs.get(job_id)
        return None

    async def update_job_status(self, job_id: str, status: str, **kwargs) -> Optional[dict]:
        """Atualiza o status de um job."""
        if hasattr(ConversionJobRepository, '_jobs') and job_id in ConversionJobRepository._jobs:
            job = ConversionJobRepository._jobs[job_id]
            job["status"] = status
            job["updated_at"] = datetime.now()
            
            # Atualizar campos específicos
            for key, value in kwargs.items():
                if key in job and value is not None:
                    job[key] = value
            
            return job
        return None

    async def get_jobs_by_user(self, professor_id: int) -> List[dict]:
        """Busca todos os jobs de um usuário."""
        if not hasattr(ConversionJobRepository, '_jobs'):
            return []
        
        user_jobs = [
            job for job in ConversionJobRepository._jobs.values()
            if job["professor_id"] == professor_id
        ]
        return user_jobs

    async def get_jobs_by_dicom(self, dicom_id: int) -> List[dict]:
        """Busca todos os jobs de um DICOM específico."""
        if not hasattr(ConversionJobRepository, '_jobs'):
            return []
        
        dicom_jobs = [
            job for job in ConversionJobRepository._jobs.values()
            if job["dicom_id"] == dicom_id
        ]
        return dicom_jobs
