import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException
from datetime import datetime

# Importa as classes do seu projeto
# Assumindo que o teste de professor está em um arquivo separado, 
# mas se estiver tudo junto, não há problema.
from app.professor.service import ProfessorService
from app.professor.schemas import ProfessorCreate, ProfessorUpdate, PasswordChangeRequest

# Marca todos os testes neste arquivo para serem executados com asyncio
pytestmark = pytest.mark.asyncio

# --- Fixtures para Mocks ---

@pytest.fixture
def mock_repository():
    """Um mock para o ProfessorRepository."""
    return AsyncMock()

@pytest.fixture
def mock_auth_service():
    """Um mock para o AuthService."""
    auth_mock = AsyncMock()
    auth_mock._hash_password.return_value = "senha_com_hash"
    
    # CORREÇÃO: O seu código de serviço chama _verify_password de forma SÍNCRONA.
    # Portanto, substituímos o método assíncrono padrão do mock por um MagicMock SÍNCRONO.
    auth_mock._verify_password = MagicMock(return_value=True)
    return auth_mock

@pytest.fixture
def professor_service(mock_repository, mock_auth_service):
    """Cria uma instância do ProfessorService com dependências mockadas."""
    return ProfessorService(repository=mock_repository, auth_service=mock_auth_service)

@pytest.fixture
def mock_professor_model():
    """Cria um objeto mock que simula o modelo do Prisma."""
    professor = MagicMock()
    professor.Professor_ID = 1
    professor.Nome = "Professor Teste"
    professor.Email = "teste@exemplo.com"
    professor.Senha = "senha_com_hash"
    professor.created_at = datetime.now()
    return professor

# --- Testes ---

async def test_create_professor_success(professor_service, mock_repository, mock_auth_service, mock_professor_model):
    """Testa a criação bem-sucedida de um professor."""
    mock_repository.email_exists.return_value = False
    mock_repository.create.return_value = mock_professor_model
    
    professor_data = ProfessorCreate(nome="Professor Teste", email="teste@exemplo.com", senha="123456")

    result = await professor_service.create_professor(professor_data)

    mock_repository.email_exists.assert_called_once_with("teste@exemplo.com")
    mock_auth_service._hash_password.assert_called_once_with("123456")
    mock_repository.create.assert_called_once()
    assert result.professor_id == 1
    assert result.nome == "Professor Teste"

async def test_create_professor_email_exists(professor_service, mock_repository):
    """Testa a falha na criação de um professor quando o email já existe."""
    mock_repository.email_exists.return_value = True
    professor_data = ProfessorCreate(nome="Professor Teste", email="existente@exemplo.com", senha="123456")

    with pytest.raises(HTTPException) as exc_info:
        await professor_service.create_professor(professor_data)

    assert exc_info.value.status_code == 400
    assert "Email já está em uso" in exc_info.value.detail

async def test_update_professor_success(professor_service, mock_repository, mock_professor_model):
    """Testa a atualização bem-sucedida do perfil pelo próprio professor."""
    mock_repository.get_by_id.return_value = mock_professor_model
    mock_repository.email_exists.return_value = False
    mock_repository.update.return_value = mock_professor_model
    
    update_data = ProfessorUpdate(nome="Professor Atualizado")
    current_user_id = 1

    result = await professor_service.update_professor(1, update_data, current_user_id)

    mock_repository.get_by_id.assert_called_once_with(1)
    mock_repository.update.assert_called_once_with(1, {"Nome": "Professor Atualizado"})
    assert result.nome == "Professor Teste"

async def test_update_professor_permission_denied(professor_service, mock_repository, mock_professor_model):
    """Testa a falha de permissão ao tentar editar outro perfil."""
    mock_repository.get_by_id.return_value = mock_professor_model
    update_data = ProfessorUpdate(nome="Nome Invasor")
    current_user_id = 99

    with pytest.raises(HTTPException) as exc_info:
        await professor_service.update_professor(1, update_data, current_user_id)

    assert exc_info.value.status_code == 403

async def test_update_professor_not_found(professor_service, mock_repository):
    """Testa a atualização de um professor que não existe."""
    mock_repository.get_by_id.return_value = None
    update_data = ProfessorUpdate(nome="Fantasma")
    
    result = await professor_service.update_professor(999, update_data, 999)
    
    assert result is None

async def test_delete_professor_success(professor_service, mock_repository, mock_professor_model):
    """Testa a exclusão bem-sucedida do perfil pelo próprio professor."""
    mock_repository.get_by_id.return_value = mock_professor_model
    mock_repository.delete.return_value = mock_professor_model
    current_user_id = 1

    result = await professor_service.delete_professor(1, current_user_id)

    assert result is True
    mock_repository.delete.assert_called_once_with(1)

async def test_delete_professor_permission_denied(professor_service, mock_repository, mock_professor_model):
    """Testa a falha de permissão ao tentar deletar outro perfil."""
    mock_repository.get_by_id.return_value = mock_professor_model
    current_user_id = 99

    with pytest.raises(HTTPException) as exc_info:
        await professor_service.delete_professor(1, current_user_id)

    assert exc_info.value.status_code == 403
    mock_repository.delete.assert_not_called()

async def test_change_password_success(professor_service, mock_repository, mock_auth_service, mock_professor_model):
    """Testa a alteração de senha bem-sucedida."""
    mock_repository.get_by_id.return_value = mock_professor_model
    mock_auth_service._verify_password.return_value = True
    
    password_data = PasswordChangeRequest(senha_atual="senha_antiga", nova_senha="senha_nova_longa")
    
    result = await professor_service.change_password(1, password_data, 1)
    
    assert result is True
    mock_auth_service._verify_password.assert_called_once_with("senha_antiga", "senha_com_hash")
    mock_auth_service._hash_password.assert_called_once_with("senha_nova_longa")
    mock_repository.update.assert_called_once()

async def test_change_password_wrong_current_password(professor_service, mock_repository, mock_auth_service, mock_professor_model):
    """Testa a falha na alteração de senha devido à senha atual incorreta."""
    mock_repository.get_by_id.return_value = mock_professor_model
    mock_auth_service._verify_password.return_value = False
    
    password_data = PasswordChangeRequest(senha_atual="senha_errada", nova_senha="senha_nova_longa")
    
    with pytest.raises(HTTPException) as exc_info:
        await professor_service.change_password(1, password_data, 1)
        
    assert exc_info.value.status_code == 400
    assert "Senha atual incorreta" in exc_info.value.detail
