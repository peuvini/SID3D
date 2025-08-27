# tests/conftest.py

import sys
import os
import pytest
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient

# Adiciona a raiz do projeto ao PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app 
from app.dependencies import get_dicom_service
from app.auth.auth_middleware import get_current_user

@pytest.fixture
def mock_dicom_service():
    return AsyncMock()

@pytest.fixture
def mock_current_user():
    user = AsyncMock()
    user.professor_id = 10
    user.id = 1
    user.email = "test@user.com"
    return user

@pytest.fixture
def client(mock_dicom_service, mock_current_user):
    """
    CORREÇÃO: Esta fixture agora passa os mocks corretamente para a aplicação.
    """
    # A fixture 'client' recebe os mocks prontos como argumentos.
    # Estas funções de override simplesmente retornam esses objetos já mockados.
    def override_get_dicom_service():
        return mock_dicom_service

    def override_get_current_user():
        return mock_current_user

    app.dependency_overrides[get_dicom_service] = override_get_dicom_service
    app.dependency_overrides[get_current_user] = override_get_current_user

    yield TestClient(app)

    app.dependency_overrides.clear()