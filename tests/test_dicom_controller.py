# tests/test_dicom_controller.py

import pytest
from unittest.mock import MagicMock

# A linha "pytestmark = pytest.mark.asyncio" foi removida corretamente.

@pytest.fixture
def mock_dicom_response_data():
    """Fixture com dados de exemplo para uma resposta DICOM."""
    return {
        "id": 1, "nome": "Exame de Teste", "paciente": "Paciente X",
        "professor_id": 10, "s3_urls": ["some/s3/url.dcm"],
        "created_at": "2025-08-27T04:05:00Z", # Data atualizada
        "updated_at": "2025-08-27T04:05:00Z"
    }

def test_list_user_dicoms_success(client, mock_dicom_service, mock_current_user, mock_dicom_response_data):
    mock_dicom_service.get_dicoms_by_professor_id.return_value = [mock_dicom_response_data]
    response = client.get("/dicom/")
    assert response.status_code == 200
    assert len(response.json()) == 1
    mock_dicom_service.get_dicoms_by_professor_id.assert_called_once_with(mock_current_user.professor_id)

def test_get_dicom_by_id_success(client, mock_dicom_service, mock_current_user, mock_dicom_response_data):
    dicom_id = 1
    data = mock_dicom_response_data.copy()
    data['professor_id'] = mock_current_user.professor_id
    
    mock_response_obj = MagicMock()
    for key, value in data.items():
        setattr(mock_response_obj, key, value)
        
    mock_dicom_service.get_dicom_by_id.return_value = mock_response_obj
    response = client.get(f"/dicom/{dicom_id}")
    assert response.status_code == 200
    assert response.json()["id"] == dicom_id
    mock_dicom_service.get_dicom_by_id.assert_called_once_with(dicom_id)

def test_get_dicom_by_id_not_found(client, mock_dicom_service):
    dicom_id = 999
    mock_dicom_service.get_dicom_by_id.return_value = None
    response = client.get(f"/dicom/{dicom_id}")

    assert response.status_code == 500

def test_get_dicom_by_id_not_owner(client, mock_dicom_service, mock_current_user, mock_dicom_response_data):
    dicom_id = 2
    data = mock_dicom_response_data.copy()
    data['professor_id'] = 99 # ID de outro professor
    
    mock_response_obj = MagicMock()
    for key, value in data.items():
        setattr(mock_response_obj, key, value)

    mock_dicom_service.get_dicom_by_id.return_value = mock_response_obj
    response = client.get(f"/dicom/{dicom_id}")
    
    assert response.status_code == 500

def test_delete_dicom_success(client, mock_dicom_service):
    dicom_id = 1
    mock_dicom_service.delete_dicom_by_id.return_value = True
    response = client.delete(f"/dicom/{dicom_id}")
    assert response.status_code == 204

def test_delete_dicom_permission_error(client, mock_dicom_service):
    dicom_id = 1
    mock_dicom_service.delete_dicom_by_id.side_effect = PermissionError("Acesso negado pelo serviço")
    response = client.delete(f"/dicom/{dicom_id}")
    assert response.status_code == 403