# app/impressora/service.py

from typing import List, Optional
from datetime import datetime
import httpx # Biblioteca moderna para requisições HTTP, ideal para interagir com APIs de impressoras

from .repository import ImpressoraRepository, ImpressaoRepository
from .schemas import ImpressoraCreate, ImpressoraResponse, ImprimirRequest, ImpressaoResponse
from app.dicom.repository import DICOMRepository


class ImpressoraService:
    def __init__(
        self, 
        impressora_repo: ImpressoraRepository, 
        impressao_repo: ImpressaoRepository,
        dicom_repo: DICOMRepository # Repositório para validar a existência do arquivo
    ):
        self.impressora_repo = impressora_repo
        self.impressao_repo = impressao_repo
        self.dicom_repo = dicom_repo

    async def _map_to_impressora_response(self, model) -> ImpressoraResponse:
        """Mapeia o modelo Prisma para o schema de resposta da Impressora."""
        if not model: return None
        return ImpressoraResponse.from_orm(model)

    async def _map_to_impressao_response(self, model) -> ImpressaoResponse:
        """Mapeia o modelo Prisma para o schema de resposta da Impressao."""
        if not model: return None
        return ImpressaoResponse.from_orm(model)

    async def _send_file_to_printer_api(self, ip: str, file_url: str):
        """
        [PLACEHOLDER] Função para enviar o arquivo para a API da impressora.
        
        Esta é uma simulação. A implementação real dependerá da API da sua impressora
        (ex: OctoPrint, Duet, Klipper, etc.).
        
        A lógica seria:
        1. Obter o arquivo (seja pelo `file_url` ou baixando do S3).
        2. Montar uma requisição HTTP POST/multipart para a API da impressora no `ip` fornecido.
        3. Enviar o arquivo e iniciar a impressão.
        4. Tratar sucessos e falhas.
        """
        print(f"SIMULAÇÃO: Enviando arquivo de {file_url} para a impressora em {ip}...")
        
        # Exemplo com httpx (código comentado, apenas para ilustração)
        # async with httpx.AsyncClient() as client:
        #     try:
        #         # Aqui você precisaria baixar o arquivo do S3 primeiro
        #         # file_content = await download_from_s3(file_key)
        #         # files = {'file': (filename, file_content, 'application/octet-stream')}
        #         # headers = {'X-Api-Key': 'SUA_API_KEY_DA_IMPRESSORA'}
        #         # response = await client.post(f"http://{ip}/api/files/local", files=files, headers=headers)
        #         # response.raise_for_status() # Lança exceção se a resposta for de erro
        #         print("SIMULAÇÃO: Arquivo enviado com sucesso.")
        #         return True
        #     except httpx.RequestError as e:
        #         print(f"SIMULAÇÃO: Erro ao conectar com a impressora: {e}")
        #         raise ConnectionError(f"Não foi possível conectar à impressora em {ip}.")
        
        # Simulação de sucesso
        return True

    async def cadastrar_impressora(self, impressora_data: ImpressoraCreate) -> ImpressoraResponse:
        """Cadastra uma nova impressora no sistema."""
        existing = await self.impressora_repo.get_by_ip(impressora_data.ip)
        if existing:
            raise ValueError(f"Já existe uma impressora cadastrada com o IP {impressora_data.ip}")

        nova_impressora = await self.impressora_repo.create_impressora(impressora_data.model_dump())
        return await self._map_to_impressora_response(nova_impressora)

    async def get_all_impressoras(self) -> List[ImpressoraResponse]:
        """Retorna todas as impressoras cadastradas."""
        impressoras = await self.impressora_repo.get_all()
        return [await self._map_to_impressora_response(i) for i in impressoras]

    async def iniciar_impressao(self, request: ImprimirRequest) -> ImpressaoResponse:
        """Orquestra o início de um trabalho de impressão."""
        # 1. Validar se a impressora e o arquivo existem
        impressora = await self.impressora_repo.get_by_id(request.impressora_id)
        if not impressora:
            raise ValueError("Impressora não encontrada.")

        arquivo_3d = await self.dicom_repo.get_dicom_by_id(request.arquivo_id)
        if not arquivo_3d:
            raise ValueError("Arquivo 3D não encontrado.")
        
        # TODO: Adicionar lógica para verificar se a impressora está disponível (não imprimindo)

        # 2. Criar o registro do trabalho de impressão (log)
        dados_impressao = {
            "impressora_id": impressora.id,
            "arquivo_3d_id": arquivo_3d.DICOM_ID,
            "data_inicio": datetime.utcnow(),
            "status": "iniciada"
        }
        novo_job = await self.impressao_repo.create_impressao(dados_impressao)

        # 3. Enviar o arquivo para a impressora (usando a função de simulação)
        try:
            # No mundo real, você precisaria de uma URL para o arquivo,
            # como a URL pré-assinada do S3 que fizemos antes.
            # Aqui, estamos usando o campo 'URL' que armazena a chave do S3.
            file_key_s3 = arquivo_3d.URL
            await self._send_file_to_printer_api(impressora.ip, file_key_s3)
        except Exception as e:
            # Se o envio falhar, atualiza o status do job e lança o erro
            await self.impressao_repo.update_status(
                novo_job.id, 
                {"status": "falhou", "data_conclusao": datetime.utcnow()}
            )
            raise e

        return await self._map_to_impressao_response(novo_job)