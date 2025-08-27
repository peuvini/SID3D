# arquivo3D/factory.py

import io
import os
import tempfile
import numpy as np
import uuid
from abc import ABC, abstractmethod
from typing import Optional, Tuple, List
from pathlib import Path

try:
    import pydicom
    import trimesh
    from scipy import ndimage
    from skimage import measure, filters, morphology
    from PIL import Image
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
    
    def get_slice_image(self, dicom_files_content: List[bytes], plane: str, slice_index: int) -> bytes:
        pass

    def get_volume_dimensions(self, dicom_files_content: List[bytes]) -> Tuple[int, int, int]:
        pass
    def edit_mesh(self, mesh_content: bytes, operation: str, box_center: List[float], box_size: List[float], output_format: str) -> bytes:
        pass

class Arquivo3DFactoryImpl(Arquivo3DAbstractFactory):
    """Implementação concreta da fábrica de geração de malhas 3D."""

    def __init__(self, iso_value: float = 100.0, smooth: bool = True,
                 smooth_iterations: int = 3):
        """
        Inicializa a factory com parâmetros de configuração.
        
        :param iso_value: Valor de isosuperfície para extração da malha (Hounsfield Units)
        :param smooth: Se deve aplicar suavização na malha gerada
        :param smooth_iterations: Número de iterações para o filtro de suavização
        """
        if not HAS_LIBS:
            raise ImportError(
                "Bibliotecas necessárias não instaladas. "
                "Execute: pip install pydicom trimesh scipy scikit-image"
            )

        self.iso_value = iso_value
        self.smooth = smooth
        self.smooth_iterations = int(smooth_iterations)

    def set_parameters(self, iso_value: Optional[float] = None, 
                       simplify_target_faces: Optional[int] = None):
        """Permite ajustar os parâmetros de geração antes de executar."""
        if iso_value is not None:
            print(f"⚙️ [FACTORY] Parâmetro 'iso_value' atualizado para: {iso_value}")
            self.iso_value = iso_value
        if simplify_target_faces is not None:
            print(f"⚙️ [FACTORY] Parâmetro 'simplify_target_faces' atualizado para: {simplify_target_faces}")
            self.simplify_target_faces = simplify_target_faces

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

        # 3.5 Validar malha e salvar debug se necessário
        try:
            self._validate_and_dump_mesh(mesh)
        except Exception as e:
            # Em caso de problema, tentar exportar debug e propagar erro com contexto
            raise ValueError(f"Malha inválida antes da exportação: {e}")
        
        # 4. Exportar no formato desejado
        print(f"💾 [FACTORY] Exportando para {file_format.upper()}...")
        result = self._export_mesh(mesh, file_format)
        print(f"✅ [FACTORY] Arquivo gerado com {len(result)} bytes")
        return result

    def _create_3d_volume(self, dicom_files_content: List[bytes]) -> np.ndarray:
        """
        Cria um volume 3D a partir dos arquivos DICOM, lidando com formatos
        single-frame e multi-frame.
        """
        slices = []

        # tentativa de inferir spacing
        px_spacing = None
        z_spacing = None

        # Processar cada arquivo DICOM
        for idx, dicom_bytes in enumerate(dicom_files_content):
            try:
                # O `force=True` pode ajudar a ler arquivos sem o cabeçalho completo
                dicom_buffer = io.BytesIO(dicom_bytes)
                dataset = pydicom.dcmread(dicom_buffer, force=True)

                if not hasattr(dataset, 'pixel_array'):
                    print("⚠️ [FACTORY] Arquivo DICOM sem pixel_array, ignorando.")
                    continue

                slice_data = dataset.pixel_array.astype(np.float32)

                # Capturar espaçamento se disponível (PixelSpacing é [row, col])
                if hasattr(dataset, 'PixelSpacing') and px_spacing is None:
                    try:
                        p = dataset.PixelSpacing
                        px_spacing = (float(p[0]), float(p[1]))
                    except Exception:
                        px_spacing = None

                if z_spacing is None:
                    if hasattr(dataset, 'SliceThickness'):
                        try:
                            z_spacing = float(dataset.SliceThickness)
                        except Exception:
                            z_spacing = None
                    elif hasattr(dataset, 'SpacingBetweenSlices'):
                        try:
                            z_spacing = float(dataset.SpacingBetweenSlices)
                        except Exception:
                            z_spacing = None

                # Aplicar transformações de Hounsfield Units se disponível
                if hasattr(dataset, 'RescaleSlope') and hasattr(dataset, 'RescaleIntercept'):
                    slice_data = slice_data * float(dataset.RescaleSlope) + float(dataset.RescaleIntercept)

                # Lidar com fatias individuais ou multi-frames
                z_position_base = 0.0
                if hasattr(dataset, 'SliceLocation'):
                    try:
                        z_position_base = float(dataset.SliceLocation)
                    except Exception:
                        z_position_base = 0.0
                elif hasattr(dataset, 'ImagePositionPatient'):
                    try:
                        z_position_base = float(dataset.ImagePositionPatient[2])
                    except Exception:
                        z_position_base = 0.0

                if slice_data.ndim == 2:
                    # É uma única fatia (2D)
                    slices.append((z_position_base, slice_data))
                elif slice_data.ndim == 3:
                    # Pode ser multi-frame (frames, H, W) ou imagem colorida (H, W, C)
                    num_frames = None
                    if hasattr(dataset, 'NumberOfFrames'):
                        try:
                            num_frames = int(dataset.NumberOfFrames)
                        except Exception:
                            num_frames = None

                    # Se NumberOfFrames disponível e bate com a primeira dimensão -> multi-frame
                    if num_frames and slice_data.shape[0] == num_frames:
                        print(f"📦 [FACTORY] Encontrado arquivo multi-frame com {slice_data.shape[0]} fatias.")
                        for i in range(slice_data.shape[0]):
                            slices.append((z_position_base + i * 0.1, slice_data[i]))
                    # Se o último eixo parece ser canais de cor (3 ou 4) -> converter para grayscale
                    elif slice_data.shape[-1] in (3, 4):
                        print("ℹ️ [FACTORY] Fatia colorida (RGB/A) detectada; convertendo para escala de cinza.")
                        try:
                            rgb = slice_data[..., :3].astype(np.float32)
                            gray = rgb[..., 0] * 0.2989 + rgb[..., 1] * 0.5870 + rgb[..., 2] * 0.1140
                            slices.append((z_position_base, gray))
                        except Exception:
                            # Fallback: colapsar média dos canais
                            gray = slice_data.mean(axis=-1)
                            slices.append((z_position_base, gray))
                    # Heurística: se a primeira dimensão é grande (ex: >4) e diferente das outras -> multi-frame
                    elif slice_data.shape[0] > 4 and slice_data.shape[0] != slice_data.shape[1]:
                        print(f"📦 [FACTORY] Interpretando como multi-frame com {slice_data.shape[0]} fatias (heurística).")
                        for i in range(slice_data.shape[0]):
                            slices.append((z_position_base + i * 0.1, slice_data[i]))
                    else:
                        print(f"⚠️ [FACTORY] Dimensão do pixel_array 3D sem formato reconhecido: {slice_data.shape}; interpretando primeiro plano como fatia.")
                        # Tenta extrair a primeira fatia ou canal
                        if slice_data.shape[-1] in (3, 4):
                            slices.append((z_position_base, slice_data[..., 0]))
                        else:
                            slices.append((z_position_base, slice_data[0]))
                else:
                    print(f"⚠️ [FACTORY] Dimensão do pixel_array não suportada: {slice_data.ndim}")

            except Exception as e:
                print(f"❌ [FACTORY] Erro ao processar arquivo DICOM idx={idx}: {e}")
                continue

        if not slices:
            raise ValueError("Nenhuma fatia DICOM válida encontrada")

        # Ordenar fatias pela posição Z
        slices.sort(key=lambda x: x[0])

        # Empilhar fatias para formar volume 3D
        volume_data = np.stack([slice_data for _, slice_data in slices], axis=0)

        # Define voxel spacing (z, y, x)
        if px_spacing is not None and z_spacing is None:
            # fallback: infer z spacing from differences in SliceLocation
            try:
                zs = [s[0] for s in slices]
                diffs = np.diff(sorted(zs))
                if len(diffs) > 0:
                    z_spacing = float(np.median(diffs))
            except Exception:
                z_spacing = 1.0

        if px_spacing is None:
            # fallback para 1.0mm
            px_spacing = (1.0, 1.0)
        if z_spacing is None:
            z_spacing = 1.0

        # armazenar espaçamento para uso posterior
        self.voxel_spacing = (z_spacing, float(px_spacing[0]), float(px_spacing[1]))

        print(f"✅ [FACTORY] Volume 3D criado com sucesso: {volume_data.shape}, voxel_spacing={self.voxel_spacing}")
        return volume_data

    def _segment_volume(self, volume: np.ndarray) -> Optional[np.ndarray]:
        """
        Segmenta o volume usando Otsu e limpezas morfológicas. Retorna máscara booleana ou None.
        """
        try:
            # Tenta Otsu
            try:
                thresh = filters.threshold_otsu(volume)
                mask = volume > thresh
            except Exception:
                # Fallback: percentile alto
                p = np.percentile(volume, 99)
                mask = volume > p

            # Limpeza morfológica básica
            mask = morphology.remove_small_objects(mask.astype(bool), min_size=64)
            mask = ndimage.binary_fill_holes(mask)

            # Seleciona o maior componente conectado
            labels, num = ndimage.label(mask)
            if num == 0:
                return None
            counts = np.bincount(labels.ravel())
            counts[0] = 0
            largest = np.argmax(counts)
            final = labels == largest

            # Fechamento para suavizar
            try:
                final = morphology.binary_closing(final, morphology.ball(2))
            except Exception:
                pass

            return final
        except Exception as e:
            print(f"[FACTORY] Segmentação falhou: {e}")
            return None

    def _extract_surface(self, volume: np.ndarray) -> trimesh.Trimesh:
        """
        Extrai superfície do volume usando algoritmo marching cubes.
        """
        print(f"🔍 [FACTORY] Volume stats - min: {volume.min():.1f}, max: {volume.max():.1f}, iso_value: {self.iso_value}")

        try:
            print("💡 [FACTORY] Usando isovalor manual para extração de superfície.")
            target_volume = volume
            iso_value = self.iso_value # Usamos o isovalue da instância

            # Verificar se o iso_value está dentro do range do volume; ajustar quando necessário
            if iso_value < volume.min() or iso_value > volume.max():
                suggested_iso = (volume.min() + volume.max()) / 2
                print(f"⚠️ [FACTORY] iso_value {iso_value} fora do range. Usando {suggested_iso:.1f}")
                mc_level = suggested_iso
            else:
                mc_level = iso_value

            spacing = getattr(self, 'voxel_spacing', None)
            mc_kwargs = dict(level=mc_level, step_size=1, allow_degenerate=False)
            if spacing is not None:
                mc_kwargs['spacing'] = spacing

            # Garantir que o nível passado para marching_cubes esteja estritamente dentro do intervalo
            vmin, vmax = float(target_volume.min()), float(target_volume.max())
            print(f"🔎 [FACTORY] Target volume range - min: {vmin:.6f}, max: {vmax:.6f}, requested level: {mc_level}")

            if vmin == vmax:
                # Tentar criar pequena variação aplicando suavização para obter gradiente
                print("⚠️ [FACTORY] Volume sem variação de intensidade. Tentando suavizar para criar variação...")
                try:
                    target_volume = ndimage.gaussian_filter(target_volume.astype(np.float32), sigma=1.0)
                    vmin, vmax = float(target_volume.min()), float(target_volume.max())
                    print(f"🔎 [FACTORY] Após suavização - min: {vmin:.6f}, max: {vmax:.6f}")
                except Exception:
                    pass

            if vmin == vmax:
                # Tentar usar magnitude do gradiente como fallback (ex.: bordas)
                print("⚠️ [FACTORY] Volume sem variação de intensidade; tentando extração por gradiente (Sobel)...")
                try:
                    # Calcular derivadas em cada eixo para obter magnitude do gradiente
                    gx = ndimage.sobel(volume.astype(np.float32), axis=0)
                    gy = ndimage.sobel(volume.astype(np.float32), axis=1)
                    gz = ndimage.sobel(volume.astype(np.float32), axis=2)
                    grad = np.sqrt(gx * gx + gy * gy + gz * gz)
                    gvmin, gvmax = float(grad.min()), float(grad.max())
                    if gvmin == gvmax:
                        raise ValueError("Gradiente também sem variação")

                    # Usar gradiente como target_volume e ajustar nível para meio do range
                    target_volume = grad
                    vmin, vmax = gvmin, gvmax
                    mc_level = vmin + (vmax - vmin) * 0.5
                    mc_kwargs['level'] = mc_level
                    print(f"🔎 [FACTORY] Usando gradiente como target_volume - min: {vmin:.6f}, max: {vmax:.6f}, level: {mc_level:.6f}")
                except Exception as e:
                    raise ValueError("Volume não apresenta variação de intensidade; impossível extrair superfície") from e

            # Ajustar mc_level para estar estritamente dentro do intervalo (min < level < max)
            if not (vmin < float(mc_level) < vmax):
                adjusted_level = vmin + (vmax - vmin) * 0.5
                print(f"⚠️ [FACTORY] Nível {mc_level} fora do intervalo do target_volume. Ajustando para {adjusted_level:.6f}")
                mc_level = adjusted_level
                mc_kwargs['level'] = mc_level

            vertices, faces, normals, _ = measure.marching_cubes(target_volume, **mc_kwargs)

            if len(vertices) == 0 or len(faces) == 0:
                print("⚠️ [FACTORY] Marching cubes não gerou malha válida, tentando com nível alternativo...")
                # Tentar com um nível alternativo no meio do range
                alt_level = vmin + (vmax - vmin) * 0.3
                mc_kwargs['level'] = alt_level
                vertices, faces, normals, _ = measure.marching_cubes(target_volume, **mc_kwargs)

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

    def _save_debug_mesh(self, mesh: trimesh.Trimesh, label: str = "debug") -> Tuple[str, str]:
        """Salva PLY e STL de debug no tmp e retorna caminhos (ply_path, stl_path)."""
        tmp = tempfile.gettempdir()
        uid = uuid.uuid4().hex[:8]
        ply_path = os.path.join(tmp, f"{label}_{uid}.ply")
        stl_path = os.path.join(tmp, f"{label}_{uid}.stl")
        try:
            ply_bytes = mesh.export(file_type='ply')
            with open(ply_path, 'wb') as f:
                if isinstance(ply_bytes, (bytes, bytearray)):
                    f.write(ply_bytes)
                else:
                    f.write(ply_bytes.encode('utf-8'))
        except Exception:
            ply_path = ""

        try:
            stl_bytes = mesh.export(file_type='stl')
            with open(stl_path, 'wb') as f:
                if isinstance(stl_bytes, (bytes, bytearray)):
                    f.write(stl_bytes)
                else:
                    f.write(stl_bytes.encode('utf-8'))
        except Exception:
            stl_path = ""

        print(f"[FACTORY] Debug meshes salvos: ply={ply_path or 'n/a'}, stl={stl_path or 'n/a'}")
        return ply_path, stl_path

    def _validate_and_dump_mesh(self, mesh: trimesh.Trimesh) -> None:
        """Valida propriedades essenciais da malha e salva arquivos de debug quando detectar problemas."""
        # Verificações básicas
        vcount = 0
        fcount = 0
        try:
            vcount = len(mesh.vertices)
            fcount = len(mesh.faces)
        except Exception:
            raise ValueError("Falha ao ler contagem de vértices/faces da malha")

        print(f"[FACTORY] Validação de malha: vértices={vcount}, faces={fcount}, is_empty={getattr(mesh, 'is_empty', False)}")

        # Se não tem faces, salvar debug e falhar
        if fcount == 0:
            ply_path, stl_path = self._save_debug_mesh(mesh, label='mesh_no_faces')
            raise ValueError(f"Malha não contém faces (0). Arquivos de debug: {ply_path}, {stl_path}")

        # Verificar NaN/Inf
        try:
            verts = np.asarray(mesh.vertices, dtype=np.float64)
            if np.isnan(verts).any() or np.isinf(verts).any():
                ply_path, stl_path = self._save_debug_mesh(mesh, label='mesh_nan_inf')
                raise ValueError(f"Malha contém NaN/Inf nos vértices. Debug: {ply_path}, {stl_path}")
        except Exception:
            ply_path, stl_path = self._save_debug_mesh(mesh, label='mesh_bad_vertices')
            raise ValueError(f"Erro ao validar vértices; debug salvo: {ply_path}, {stl_path}")

    def _smooth_mesh(self, mesh: trimesh.Trimesh) -> trimesh.Trimesh:
        """
        Aplica suavização na malha usando filtro Laplaciano.
        """
        try:
            # Aplicar suavização com número controlado de iterações
            from trimesh.smoothing import filter_laplacian
            iterations = max(0, self.smooth_iterations) # Usar 0 para desabilitar
            
            if iterations > 0:
                print(f"[FACTORY] Aplicando filter_laplacian por {iterations} iterações...")
                mesh = filter_laplacian(mesh, iterations=iterations)
            else:
                print("[FACTORY] Suavização desabilitada (smooth_iterations = 0).")

            return mesh
        except Exception as e:
            print(f"Aviso: Erro na suavização da malha: {e}")
            # Fallback para o método mais simples se o filtro laplaciano falhar
            if self.smooth_iterations > 0:
                return mesh.smoothed()
            return mesh

    def _export_mesh(self, mesh: trimesh.Trimesh, file_format: str) -> bytes:
        """
        Exporta a malha no formato especificado.
        """
        format_lower = file_format.lower()
        try:
            if format_lower == "stl":
                data = mesh.export(file_type='stl')
            elif format_lower == "obj":
                data = mesh.export(file_type='obj')
            elif format_lower == "ply":
                data = mesh.export(file_type='ply')
            else:
                # Default para STL
                data = mesh.export(file_type='stl')

            # Normalizar para bytes
            if isinstance(data, (bytes, bytearray)):
                out = bytes(data)
            else:
                out = str(data).encode('utf-8')

            # Checar tamanho mínimo razoável (ex: header apenas pode estar muito pequeno)
            if len(out) < 100:
                print(f"[FACTORY] Aviso: export result muito pequeno ({len(out)} bytes) para formato {file_format}")
            return out

        except Exception as e:
            # Tentar salvar debug antes de propagar
            try:
                self._save_debug_mesh(mesh, label='export_error')
            except Exception:
                pass
            raise ValueError(f"Erro ao exportar malha no formato {file_format}: {e}")

    def get_slice_image(self, dicom_files_content: List[bytes], plane: str, slice_index: int) -> bytes:
        """
        Gera uma imagem PNG de uma fatia específica do volume DICOM.
        """
        if not dicom_files_content:
            raise ValueError("Nenhum arquivo DICOM fornecido para gerar fatia")

        # 1. Criar o volume 3D (reutilizando a lógica existente)
        volume_3d = self._create_3d_volume(dicom_files_content)

        # 2. Obter a fatia 2D com base no plano e no índice
        slice_data = self._extract_slice_data(volume_3d, plane, slice_index)

        # 3. Normalizar e converter para imagem PNG
        normalized_slice = self._normalize_to_image(slice_data)
        img = Image.fromarray(normalized_slice)

        # 4. Salvar imagem em um buffer de bytes e retornar
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer.getvalue()

    def get_volume_dimensions(self, dicom_files_content: List[bytes]) -> Tuple[int, int, int]:
        """
        Cria o volume 3D e retorna suas dimensões (profundidade, altura, largura).
        """
        if not dicom_files_content:
            raise ValueError("Nenhum arquivo DICOM fornecido para obter dimensões")
        volume_3d = self._create_3d_volume(dicom_files_content)
        return volume_3d.shape

    def _extract_slice_data(self, volume: np.ndarray, plane: str, index: int) -> np.ndarray:
        """Extrai a fatia 2D do volume 3D."""
        if plane == "axial":
            if not 0 <= index < volume.shape[0]:
                raise IndexError(f"Índice Axial {index} fora do intervalo [0, {volume.shape[0]-1}]")
            return volume[index, :, :]
        elif plane == "coronal":
            if not 0 <= index < volume.shape[1]:
                raise IndexError(f"Índice Coronal {index} fora do intervalo [0, {volume.shape[1]-1}]")
            return volume[:, index, :]
        elif plane == "sagittal":
            if not 0 <= index < volume.shape[2]:
                raise IndexError(f"Índice Sagital {index} fora do intervalo [0, {volume.shape[2]-1}]")
            return volume[:, :, index]
        else:
            raise ValueError("Plano inválido. Use 'axial', 'coronal' ou 'sagittal'.")

    def _normalize_to_image(self, slice_data: np.ndarray) -> np.ndarray:
        """Normaliza os dados da fatia para o intervalo [0, 255] e converte para uint8."""
        min_val, max_val = slice_data.min(), slice_data.max()
        if min_val == max_val: # Evita divisão por zero
            return np.zeros(slice_data.shape, dtype=np.uint8)
        
        normalized = np.interp(slice_data, (min_val, max_val), (0, 255))
        return normalized.astype(np.uint8)
    
    def edit_mesh(self, mesh_content: bytes, operation: str, box_center: List[float], box_size: List[float], output_format: str) -> bytes:
        """
        Edita uma malha carregada aplicando uma operação booleana com uma caixa.
        
        :param mesh_content: Conteúdo binário do arquivo STL/OBJ/PLY original.
        :param operation: 'intersect' ou 'difference'.
        :param box_center: Centro da caixa de edição [x, y, z].
        :param box_size: Tamanho da caixa de edição [w, d, h].
        :param output_format: Formato de saída desejado ('stl', 'obj', 'ply').
        :return: Conteúdo binário da nova malha editada.
        """
        print(f"⚙️ [FACTORY] Iniciando edição de malha com operação: {operation.upper()}")

        # 1. Carregar a malha original a partir do conteúdo em memória
        try:
            # Usamos um file-like object para que o trimesh possa identificar o formato
            with io.BytesIO(mesh_content) as f:
                original_mesh = trimesh.load(f, file_type=output_format)
        except Exception as e:
            raise ValueError(f"Não foi possível carregar a malha original: {e}")

        # 2. Criar a "ferramenta" de edição (a caixa)
        transform = trimesh.transformations.translation_matrix(box_center)
        editing_box = trimesh.creation.box(extents=box_size, transform=transform)

        # 3. Aplicar a operação booleana
        if operation == "intersect":
            print(f"🔪 [FACTORY] Aplicando INTERSECT com caixa de tamanho {box_size} em {box_center}")
            edited_mesh = original_mesh.intersection(editing_box)
        elif operation == "difference":
            print(f"🔪 [FACTORY] Aplicando DIFFERENCE com caixa de tamanho {box_size} em {box_center}")
            edited_mesh = original_mesh.difference(editing_box)
        else:
            raise ValueError(f"Operação de edição desconhecida: {operation}")

        # Se a operação resultar em uma malha vazia, levanta um erro
        if not isinstance(edited_mesh, trimesh.Trimesh) or edited_mesh.is_empty:
            raise ValueError("A operação de edição resultou em uma malha vazia. A área de interesse pode não ter sobreposição com o modelo.")

        # 4. Exportar a malha editada para o formato de saída
        print(f"✅ [FACTORY] Edição concluída. Exportando para {output_format.upper()}...")
        return self._export_mesh(edited_mesh, output_format)

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