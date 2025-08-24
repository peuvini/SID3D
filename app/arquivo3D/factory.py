# arquivo3D/factory.py

import io
import os
import tempfile
import numpy as np
from abc import ABC, abstractmethod
from typing import List
from pathlib import Path

try:
    import pydicom
    import trimesh
    from scipy import ndimage
    from skimage import measure
    HAS_LIBS = True
except ImportError:
    HAS_LIBS = False

class Arquivo3DAbstractFactory(ABC):
    """Interface abstrata para a geração de malhas 3D a partir de arquivos DICOM."""

    @abstractmethod
    def generate(self, dicom_files_content: List[bytes], file_format: str = "stl") -> bytes:
        """
        Gera um arquivo 3D (ex: STL, OBJ, PLY) a partir de uma lista de conteúdos de arquivos DICOM.

        :param dicom_files_content: Uma lista de bytes, onde cada item é o conteúdo de um arquivo DICOM.
        :param file_format: Formato do arquivo 3D desejado (stl, obj, ply).
        :return: O conteúdo do arquivo 3D gerado, em bytes.
        """
        pass

class Arquivo3DFactoryImpl(Arquivo3DAbstractFactory):
    """Implementação concreta da fábrica de geração de malhas 3D."""

    def __init__(self, iso_value: float = 100.0, smooth: bool = True):
        """
        Inicializa a factory com parâmetros de configuração.
        
        :param iso_value: Valor de isosuperfície para extração da malha (Hounsfield Units)
        :param smooth: Se deve aplicar suavização na malha gerada
        """
        if not HAS_LIBS:
            raise ImportError(
                "Bibliotecas necessárias não instaladas. "
                "Execute: pip install pydicom trimesh scipy scikit-image"
            )
        
        self.iso_value = iso_value
        self.smooth = smooth

    def generate(self, dicom_files_content: List[bytes], file_format: str = "stl") -> bytes:
        """
        Converte arquivos DICOM em uma malha 3D usando marching cubes.
        """
        print(f"🔧 [FACTORY] Iniciando conversão de {len(dicom_files_content)} arquivos DICOM para {file_format.upper()}")
        
        if not dicom_files_content:
            raise ValueError("Nenhum arquivo DICOM fornecido")

        # 1. Processar arquivos DICOM e criar volume 3D
        print("📊 [FACTORY] Criando volume 3D...")
        volume_3d = self._create_3d_volume(dicom_files_content)
        print(f"📊 [FACTORY] Volume criado com dimensões: {volume_3d.shape}")
        
        # 2. Extrair superfície usando marching cubes
        print("🔺 [FACTORY] Extraindo superfície com marching cubes...")
        mesh = self._extract_surface(volume_3d)
        print(f"🔺 [FACTORY] Malha criada com {len(mesh.vertices)} vértices e {len(mesh.faces)} faces")
        
        # 3. Aplicar pós-processamento
        if self.smooth:
            print("✨ [FACTORY] Aplicando suavização...")
            mesh = self._smooth_mesh(mesh)
        
        # 4. Exportar no formato desejado
        print(f"💾 [FACTORY] Exportando para {file_format.upper()}...")
        result = self._export_mesh(mesh, file_format)
        print(f"✅ [FACTORY] Arquivo gerado com {len(result)} bytes")
        return result

    def _create_3d_volume(self, dicom_files_content: List[bytes]) -> np.ndarray:
        """
        Cria um volume 3D a partir dos arquivos DICOM.
        """
        slices = []
        
        # Processar cada arquivo DICOM
        for dicom_bytes in dicom_files_content:
            try:
                # Carregar DICOM do buffer de bytes
                dicom_buffer = io.BytesIO(dicom_bytes)
                dataset = pydicom.dcmread(dicom_buffer)
                
                # Extrair dados da imagem
                if hasattr(dataset, 'pixel_array'):
                    slice_data = dataset.pixel_array.astype(np.float32)
                    
                    # Aplicar transformações de Hounsfield Units se disponível
                    if hasattr(dataset, 'RescaleSlope') and hasattr(dataset, 'RescaleIntercept'):
                        slope = float(dataset.RescaleSlope)
                        intercept = float(dataset.RescaleIntercept)
                        slice_data = slice_data * slope + intercept
                    
                    # Armazenar fatia com posição Z se disponível
                    z_position = 0
                    if hasattr(dataset, 'SliceLocation'):
                        z_position = float(dataset.SliceLocation)
                    elif hasattr(dataset, 'ImagePositionPatient'):
                        z_position = float(dataset.ImagePositionPatient[2])
                    
                    slices.append((z_position, slice_data))
                    
            except Exception as e:
                print(f"Erro ao processar arquivo DICOM: {e}")
                continue
        
        if not slices:
            raise ValueError("Nenhuma fatia DICOM válida encontrada")
        
        # Ordenar fatias pela posição Z
        slices.sort(key=lambda x: x[0])
        
        # Empilhar fatias para formar volume 3D
        volume_data = np.stack([slice_data for _, slice_data in slices], axis=0)
        
        print(f"Volume 3D criado: {volume_data.shape}")
        return volume_data

    def _extract_surface(self, volume: np.ndarray) -> trimesh.Trimesh:
        """
        Extrai superfície do volume usando algoritmo marching cubes.
        """
        print(f"🔍 [FACTORY] Volume stats - min: {volume.min():.1f}, max: {volume.max():.1f}, iso_value: {self.iso_value}")
        
        # Verificar se o iso_value está dentro do range do volume
        if self.iso_value < volume.min() or self.iso_value > volume.max():
            # Ajustar iso_value automaticamente para um valor médio
            suggested_iso = (volume.min() + volume.max()) / 2
            print(f"⚠️ [FACTORY] iso_value {self.iso_value} fora do range. Usando {suggested_iso:.1f}")
            iso_value = suggested_iso
        else:
            iso_value = self.iso_value
        
        try:
            # Aplicar marching cubes para extrair superfície
            vertices, faces, normals, _ = measure.marching_cubes(
                volume, 
                level=iso_value,
                step_size=1,
                allow_degenerate=False
            )
            
            if len(vertices) == 0 or len(faces) == 0:
                print("⚠️ [FACTORY] Marching cubes não gerou malha válida, tentando com iso_value menor...")
                # Tentar com um valor menor
                iso_value = volume.min() + (volume.max() - volume.min()) * 0.3
                vertices, faces, normals, _ = measure.marching_cubes(
                    volume, 
                    level=iso_value,
                    step_size=1,
                    allow_degenerate=False
                )
            
            # Criar malha trimesh
            mesh = trimesh.Trimesh(
                vertices=vertices,
                faces=faces,
                vertex_normals=normals
            )
            
            # Remover componentes não conectados pequenos
            mesh = self._remove_small_components(mesh)
            
            print(f"Malha extraída: {len(mesh.vertices)} vértices, {len(mesh.faces)} faces")
            return mesh
            
        except Exception as e:
            raise ValueError(f"Erro na extração de superfície: {e}")

    def _remove_small_components(self, mesh: trimesh.Trimesh, min_faces: int = 100) -> trimesh.Trimesh:
        """
        Remove componentes pequenos da malha.
        """
        components = mesh.split(only_watertight=False)
        
        if len(components) == 1:
            return mesh
        
        # Manter apenas componentes com número mínimo de faces
        large_components = [comp for comp in components if len(comp.faces) >= min_faces]
        
        if not large_components:
            return mesh  # Retorna original se todos componentes são pequenos
        
        # Retorna o maior componente
        largest_component = max(large_components, key=lambda x: len(x.faces))
        return largest_component

    def _smooth_mesh(self, mesh: trimesh.Trimesh) -> trimesh.Trimesh:
        """
        Aplica suavização na malha usando filtro Laplaciano.
        """
        try:
            # Aplicar suavização simples
            mesh = mesh.smoothed()
            
            # Simplificar malha se muito densa
            if len(mesh.faces) > 50000:
                mesh = mesh.simplify_quadric_decimation(face_count=25000)
            
            return mesh
        except Exception as e:
            print(f"Aviso: Erro na suavização da malha: {e}")
            return mesh

    def _export_mesh(self, mesh: trimesh.Trimesh, file_format: str) -> bytes:
        """
        Exporta a malha no formato especificado.
        """
        format_lower = file_format.lower()
        
        try:
            if format_lower == "stl":
                return mesh.export(file_type='stl')
            elif format_lower == "obj":
                return mesh.export(file_type='obj').encode('utf-8')
            elif format_lower == "ply":
                return mesh.export(file_type='ply')
            else:
                # Default para STL
                return mesh.export(file_type='stl')
                
        except Exception as e:
            raise ValueError(f"Erro ao exportar malha no formato {file_format}: {e}")


class Arquivo3DFactoryDummy(Arquivo3DAbstractFactory):
    """Implementação dummy para testes sem dependências externas."""

    def generate(self, dicom_files_content: List[bytes], file_format: str = "stl") -> bytes:
        """
        Gera arquivos 3D dummy para testes.
        """
        print(f"[DUMMY] Gerando arquivo 3D ({file_format.upper()}) a partir de {len(dicom_files_content)} arquivos DICOM.")
        
        # Conteúdo dummy baseado no formato
        if file_format.lower() == "stl":
            content = b"""solid DummyMesh
facet normal 0 0 1
  outer loop
    vertex 0.0 0.0 0.0
    vertex 1.0 0.0 0.0
    vertex 0.5 1.0 0.0
  endloop
endfacet
facet normal 0 0 1
  outer loop
    vertex 0.0 0.0 0.0
    vertex 0.5 1.0 0.0
    vertex -0.5 1.0 0.0
  endloop
endfacet
endsolid DummyMesh
"""
        elif file_format.lower() == "obj":
            content = b"""# OBJ File Generated from DICOM (Dummy)
# Generated by SID3D Factory
v 0.0 0.0 0.0
v 1.0 0.0 0.0
v 0.5 1.0 0.0
v -0.5 1.0 0.0
vn 0.0 0.0 1.0
f 1//1 2//1 3//1
f 1//1 3//1 4//1
"""
        elif file_format.lower() == "ply":
            content = b"""ply
format ascii 1.0
element vertex 4
property float x
property float y
property float z
element face 2
property list uchar int vertex_indices
end_header
0.0 0.0 0.0
1.0 0.0 0.0
0.5 1.0 0.0
-0.5 1.0 0.0
3 0 1 2
3 0 2 3
"""
        else:
            content = b"dummy 3d file content"
        
        return content