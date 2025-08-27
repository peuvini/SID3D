import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from app.main import app 
from app.dependencies import get_professor_service
from app.auth.auth_middleware import get_current_user

@pytest.fixture
def mock_professor_service():
    return AsyncMock()

@pytest.fixture
def mock_current_user():
    user = MagicMock()
    user.professor_id = 1
    return user

@pytest.fixture
def client(mock_professor_service, mock_current_user):
    def override_get_professor_service():
        return mock_professor_service
    def override_get_current_user():
        return mock_current_user
    app.dependency_overrides[get_professor_service] = override_get_professor_service
    app.dependency_overrides[get_current_user] = override_get_current_user
    yield TestClient(app)
    app.dependency_overrides.clear()

def test_get_professor_by_id_success(client, mock_professor_service):
    """Testa GET /professor/{id} com sucesso."""
    # CORREÇÃO: O mock agora retorna um payload completo que corresponde ao ProfessorResponse.
    mock_professor_service.get_professor_by_id.return_value = {
        "professor_id": 2,
        "nome": "Outro Professor",
        "email": "outro@exemplo.com",
        "created_at": datetime.now().isoformat()
    }
    response = client.get("/professor/2")
    assert response.status_code == 200
    assert response.json()["professor_id"] == 2

def test_create_professor_success(client, mock_professor_service):
    """Testa POST /professor com sucesso."""
    # CORREÇÃO: O mock agora retorna um dicionário completo e válido, em vez de um MagicMock.
    mock_professor_service.create_professor.return_value = {
        "professor_id": 10,
        "nome": "Novo Professor",
        "email": "novo@exemplo.com",
        "created_at": datetime.now().isoformat()
    }
    professor_data = {"nome": "Novo Professor", "email": "novo@exemplo.com", "senha": "uma_senha_forte"}
    response = client.post("/professor/", json=professor_data)
    assert response.status_code == 201
    assert response.json()["professor_id"] == 10

def test_update_professor_success(client, mock_professor_service, mock_current_user):
    """Testa PUT /professor/{id} com sucesso."""
    # CORREÇÃO: O mock agora retorna um payload completo.
    mock_professor_service.update_professor.return_value = {
        "professor_id": 1,
        "nome": "Nome Atualizado",
        "email": "logado@exemplo.com",
        "created_at": datetime.now().isoformat()
    }
    update_data = {"nome": "Nome Atualizado"}
    response = client.put(f"/professor/{mock_current_user.professor_id}", json=update_data)
    assert response.status_code == 200
    assert response.json()["nome"] == "Nome Atualizado"

def test_get_my_profile_success(client, mock_professor_service):
    mock_professor_service.get_professor_by_id.return_value = {
        "professor_id": 1, "nome": "Professor Logado", "email": "logado@exemplo.com",
        "created_at": datetime.now().isoformat()
    }
    response = client.get("/professor/me")
    assert response.status_code == 200
    # CORREÇÃO: A variável 'data' não estava definida; agora usamos o JSON da resposta.
    assert response.json()["professor_id"] == 1

def test_get_professor_by_id_not_found(client, mock_professor_service):
    mock_professor_service.get_professor_by_id.return_value = None
    response = client.get("/professor/999")
    assert response.status_code == 404

def test_delete_professor_success(client, mock_professor_service, mock_current_user):
    mock_professor_service.delete_professor.return_value = True
    response = client.delete(f"/professor/{mock_current_user.professor_id}")
    assert response.status_code == 204

def test_delete_professor_not_found(client, mock_professor_service, mock_current_user):
    mock_professor_service.delete_professor.return_value = False
    response = client.delete(f"/professor/{mock_current_user.professor_id}")
    assert response.status_code == 404
