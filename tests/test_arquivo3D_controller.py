import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

# Importa o app FastAPI e as dependências que serão sobrescritas
from app.main import app 
from app.dependencies import get_arquivo3d_service
from app.auth.auth_middleware import get_current_user

# --- Fixtures e Configuração ---

@pytest.fixture
def mock_arquivo3d_service():
    """Mock para o Arquivo3DService."""
    return AsyncMock()

@pytest.fixture
def mock_current_user():
    """Mock para o usuário autenticado."""
    user = MagicMock()
    user.professor_id = 10
    return user

@pytest.fixture
def client(mock_arquivo3d_service, mock_current_user):
    """Cria um TestClient com as dependências mockadas."""
    
    def override_get_arquivo3d_service():
        return mock_arquivo3d_service

    def override_get_current_user():
        return mock_current_user

    app.dependency_overrides[get_arquivo3d_service] = override_get_arquivo3d_service
    app.dependency_overrides[get_current_user] = override_get_current_user

    yield TestClient(app)

    app.dependency_overrides.clear()

@pytest.fixture
def mock_arquivo3d_response_data():
    """Dados de exemplo para uma resposta Arquivo3DResponse."""
    return {
        "id": 100,
        "dicom_id": 1,
        "s3_url": "3d-files/path/to/file.stl",
        "file_format": "stl",
        "file_size": 12345,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }

# --- Testes ---

def test_converter_dicom_success(client, mock_arquivo3d_service, mock_arquivo3d_response_data):
    """Testa POST /arquivo3d/convert com sucesso."""
    mock_arquivo3d_service.converter_dicom_para_3d.return_value = mock_arquivo3d_response_data
    
    request_data = {"dicom_id": 1, "file_format": "stl"}
    response = client.post("/arquivo3d/convert", json=request_data)
    
    assert response.status_code == 201
    assert response.json()["id"] == 100
    mock_arquivo3d_service.converter_dicom_para_3d.assert_called_once()

def test_get_all_files(client, mock_arquivo3d_service, mock_arquivo3d_response_data):
    """Testa GET /arquivo3d/ com sucesso."""
    mock_arquivo3d_service.get_all_files.return_value = [mock_arquivo3d_response_data]
    
    response = client.get("/arquivo3d/")
    
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == 100
    mock_arquivo3d_service.get_all_files.assert_called_once_with(None)

def test_get_all_files_only_mine(client, mock_arquivo3d_service, mock_current_user):
    """Testa GET /arquivo3d/?only_mine=true com sucesso."""
    mock_arquivo3d_service.get_all_files.return_value = []

    response = client.get("/arquivo3d/?only_mine=true")

    assert response.status_code == 200
    mock_arquivo3d_service.get_all_files.assert_called_once_with(mock_current_user.professor_id)

def test_get_file_by_id_not_found(client, mock_arquivo3d_service):
    """Testa GET /arquivo3d/{id} para um arquivo que não existe."""
    mock_arquivo3d_service.get_file_by_id.return_value = None
    
    response = client.get("/arquivo3d/999")
    
    assert response.status_code == 404
    assert "não encontrado" in response.json()["detail"]

def test_delete_file_success(client, mock_arquivo3d_service, mock_current_user):
    """Testa DELETE /arquivo3d/{id} com sucesso."""
    mock_arquivo3d_service.delete_file.return_value = True
    
    response = client.delete("/arquivo3d/100")
    
    assert response.status_code == 204
    mock_arquivo3d_service.delete_file.assert_called_once_with(100, mock_current_user.professor_id)

def test_get_slice_image_success(client, mock_arquivo3d_service):
    """Testa GET /arquivo3d/slice/{dicom_id} com sucesso."""
    mock_arquivo3d_service.get_slice_image.return_value = b"fake_png_bytes"
    
    response = client.get("/arquivo3d/slice/1?plane=axial&index=50")
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content == b"fake_png_bytes"

def test_edit_file_success(client, mock_arquivo3d_service, mock_arquivo3d_response_data):
    """Testa POST /arquivo3d/{id}/edit com sucesso."""
    # O serviço retorna os dados do *novo* arquivo criado
    new_file_data = mock_arquivo3d_response_data.copy()
    new_file_data["id"] = 101 
    mock_arquivo3d_service.edit_3d_file.return_value = new_file_data

    edit_data = {
        "operation": "intersect",
        "box_center": [10, 20, 30],
        "box_size": [5, 5, 5]
    }
    response = client.post("/arquivo3d/100/edit", json=edit_data)

    assert response.status_code == 201
    assert response.json()["id"] == 101
    mock_arquivo3d_service.edit_3d_file.assert_called_once()
