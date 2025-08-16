# app/utils/mesh_generator.py

from abc import ABC, abstractmethod

class MeshGeneratorAbstract(ABC):
    """
    Classe abstrata que define a interface para qualquer serviço
    de geração de malha 3D (ex: a partir de arquivos DICOM).
    """

    @abstractmethod
    def convert_to_mesh(self, source_file_key: str):
        """
        Este método receberá a chave de um arquivo (ex: do S3)
        e iniciará o processo de conversão para uma malha 3D (STL, OBJ, etc.).
        """
        raise NotImplementedError