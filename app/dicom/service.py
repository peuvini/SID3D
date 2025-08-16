# app/dicom/service.py

import os
import aiofiles
from typing import List, Optional, Tuple
from uuid import uuid4
from fastapi import UploadFile

from .repository import DICOMRepository
from .schemas import DICOMCreate, DICOMUpdate, DICOMResponse, DICOMSearch
# O seu diagrama menciona um 'MeshGeneratorAbstract'. Vamos criar um placeholder.
# Este seria o local para integrar a lógica de conversão para malha 3D.
from app.utils.mesh_generator import MeshGeneratorAbstract 

# Defina o diretório de uploads. Crie este diretório na raiz do seu projeto.
UPLOAD_DIRECTORY = "./uploads/dicom"
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

class DICOMService:
    def __init__(self, repository: DICOMRepository, mesh_generator: MeshGeneratorAbstract):
        self.repository = repository
        self.mesh_generator = mesh_generator

    async def _map_to_response(self, dicom_model) -> DICOMResponse:
        """Helper para mapear o modelo do Prisma para o schema de resposta."""
        if not dicom_model:
            return None
        return DICOMResponse(
            dicom_id=dicom_model.DICOM_ID,
            nome=dicom_model.Nome,
            paciente=dicom_model.Paciente,
            url=dicom_model.URL,
            professor_id=dicom_model.Professor_ID,
        )

    async def create_dicom_upload(self, file: UploadFile, dicom_data: DICOMCreate) -> DICOMResponse:
        """
        Salva o arquivo DICOM fisicamente e cria o registro de metadados no banco.
        """
        # 1. Salvar o arquivo físico
        # Gera um nome de arquivo único para evitar colisões
        file_extension = file.filename.split('.')[-1]
        unique_filename = f"{uuid4()}.{file_extension}"
        file_path = os.path.join(UPLOAD_DIRECTORY, unique_filename)

        try:
            async with aiofiles.open(file_path, 'wb') as out_file:
                content = await file.read()
                await out_file.write(content)
        except Exception as e:
            # Lidar com erro de escrita de arquivo
            raise IOError(f"Não foi possível salvar o arquivo: {e}")

        # 2. Preparar dados para o repositório
        # O URL aponta para o endpoint de download, que servirá o arquivo.
        db_data = {
            "Nome": dicom_data.nome,
            "Paciente": dicom_data.paciente,
            "URL": f"/dicom/{unique_filename}", # URL relativo para download
            "Professor_ID": dicom_data.professor_id
        }
        
        # 3. Criar registro no banco
        new_dicom = await self.repository.create_dicom(db_data)
        
        # Opcional: Aqui você poderia iniciar a conversão para malha 3D em background
        # self.mesh_generator.convert_to_mesh(file_path)

        return await self._map_to_response(new_dicom)

    async def get_dicom_file_by_id(self, dicom_id: int) -> Optional[Tuple[str, str]]:
        """
        Busca os metadados do DICOM e retorna o caminho do arquivo e o nome original.
        """
        dicom_record = await self.repository.get_dicom_by_id(dicom_id)
        if not dicom_record:
            return None

        # O nome do arquivo está no final da URL
        filename = os.path.basename(dicom_record.URL)
        file_path = os.path.join(UPLOAD_DIRECTORY, filename)
        
        if not os.path.exists(file_path):
            # Lidar com o caso em que o registro existe mas o arquivo não
            raise FileNotFoundError("Arquivo físico não encontrado no servidor.")
            
        return (file_path, dicom_record.Nome)

    async def get_all_dicoms(self) -> List[DICOMResponse]:
        """Retorna uma lista de todos os metadados DICOM."""
        dicoms = await self.repository.get_all_dicoms()
        return [await self._map_to_response(d) for d in dicoms]

    async def search_dicoms(self, search_params: DICOMSearch) -> List[DICOMResponse]:
        """Busca por metadados DICOM com base em parâmetros."""
        search_criteria = {
            "Nome": search_params.nome,
            "Paciente": search_params.paciente,
            "Professor_ID": search_params.professor_id
        }
        dicoms = await self.repository.find_dicoms(search_criteria)
        return [await self._map_to_response(d) for d in dicoms]
    
    async def delete_dicom_by_id(self, dicom_id: int, current_user_professor_id: int) -> bool:
        """Deleta os metadados e o arquivo físico associado."""
        dicom_to_delete = await self.repository.get_dicom_by_id(dicom_id)
        if not dicom_to_delete:
            return False # Já não existe

        # Regra de negócio: apenas o professor que fez o upload pode deletar
        if dicom_to_delete.Professor_ID != current_user_professor_id:
            raise PermissionError("Você não tem permissão para deletar este arquivo.")

        # Deleta o registro do banco
        deleted_record = await self.repository.delete_dicom(dicom_id)
        
        # Se o registro foi deletado, apaga o arquivo físico
        if deleted_record:
            try:
                filename = os.path.basename(deleted_record.URL)
                file_path = os.path.join(UPLOAD_DIRECTORY, filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                # Logar o erro, mas a operação principal (deleção no DB) foi um sucesso
                print(f"Alerta: não foi possível apagar o arquivo físico {file_path}. Erro: {e}")
        
        return deleted_record is not None