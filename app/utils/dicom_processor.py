import io
import pydicom
import numpy as np
from PIL import Image
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

def extract_dicom_preview(dicom_content: bytes) -> Optional[bytes]:
    """
    Extrai uma imagem de preview de um arquivo DICOM.
    
    Args:
        dicom_content: Conteúdo do arquivo DICOM em bytes
        
    Returns:
        Bytes da imagem de preview em formato PNG ou None se não conseguir extrair
    """
    try:
        # Carrega o arquivo DICOM
        dicom_file = pydicom.dcmread(io.BytesIO(dicom_content))
        
        # Verifica se o arquivo tem dados de pixel
        if not hasattr(dicom_file, 'pixel_array'):
            logger.warning("Arquivo DICOM não possui dados de pixel")
            return None
            
        # Obtém o array de pixels
        pixel_array = dicom_file.pixel_array
        
        # Se for 3D, pega o slice do meio
        if len(pixel_array.shape) == 3:
            slice_index = pixel_array.shape[0] // 2
            pixel_array = pixel_array[slice_index]
        
        # Normaliza os valores para 0-255
        if pixel_array.dtype != np.uint8:
            pixel_array = normalize_pixel_array(pixel_array)
        
        # Converte para imagem PIL
        image = Image.fromarray(pixel_array)
        
        # Redimensiona para um tamanho razoável (mantendo proporção)
        max_size = (512, 512)
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Converte para bytes em formato PNG
        img_buffer = io.BytesIO()
        image.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        return img_buffer.getvalue()
        
    except Exception as e:
        logger.error(f"Erro ao extrair preview do DICOM: {str(e)}")
        return None

def normalize_pixel_array(pixel_array: np.ndarray) -> np.ndarray:
    """
    Normaliza um array de pixels para o range 0-255.
    
    Args:
        pixel_array: Array de pixels do DICOM
        
    Returns:
        Array normalizado em uint8
    """
    # Remove outliers extremos
    p2, p98 = np.percentile(pixel_array, (2, 98))
    pixel_array = np.clip(pixel_array, p2, p98)
    
    # Normaliza para 0-255
    pixel_array = ((pixel_array - pixel_array.min()) / 
                   (pixel_array.max() - pixel_array.min()) * 255).astype(np.uint8)
    
    return pixel_array

def get_dicom_metadata(dicom_content: bytes) -> dict:
    """
    Extrai metadados básicos de um arquivo DICOM.
    
    Args:
        dicom_content: Conteúdo do arquivo DICOM em bytes
        
    Returns:
        Dicionário com metadados do DICOM
    """
    try:
        dicom_file = pydicom.dcmread(io.BytesIO(dicom_content))
        
        metadata = {}
        
        # Informações do paciente
        if hasattr(dicom_file, 'PatientName'):
            metadata['patient_name'] = str(dicom_file.PatientName)
        
        if hasattr(dicom_file, 'PatientID'):
            metadata['patient_id'] = str(dicom_file.PatientID)
            
        # Informações do estudo
        if hasattr(dicom_file, 'StudyDescription'):
            metadata['study_description'] = str(dicom_file.StudyDescription)
            
        if hasattr(dicom_file, 'SeriesDescription'):
            metadata['series_description'] = str(dicom_file.SeriesDescription)
            
        # Informações técnicas
        if hasattr(dicom_file, 'Modality'):
            metadata['modality'] = str(dicom_file.Modality)
            
        if hasattr(dicom_file, 'Manufacturer'):
            metadata['manufacturer'] = str(dicom_file.Manufacturer)
            
        # Dimensões
        if hasattr(dicom_file, 'Rows') and hasattr(dicom_file, 'Columns'):
            metadata['dimensions'] = f"{dicom_file.Rows}x{dicom_file.Columns}"
            
        return metadata
        
    except Exception as e:
        logger.error(f"Erro ao extrair metadados do DICOM: {str(e)}")
        return {}
