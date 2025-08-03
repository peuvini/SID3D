#!/usr/bin/env python3
"""
Script de teste para demonstrar o uso da API SID3D
"""

import requests
import json

BASE_URL = "http://localhost:8000"


def test_health():
    """Testa o endpoint de saúde da API"""
    print("🔍 Testando endpoint de saúde...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Resposta: {response.json()}\n")


def test_register():
    """Testa o registro de usuário"""
    print("📝 Testando registro de usuário...")
    
    user_data = {
        "nome": "João Silva",
        "email": "joao@exemplo.com",
        "senha": "123456"
    }
    
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json=user_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Usuário registrado: {result['user']['nome']}")
        print(f"Token: {result['token']['access_token'][:50]}...")
        return result['token']['access_token']
    else:
        print(f"Erro: {response.json()}")
        return None


def test_login():
    """Testa o login de usuário"""
    print("🔐 Testando login de usuário...")
    
    login_data = {
        "email": "joao@exemplo.com",
        "senha": "123456"
    }
    
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json=login_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Login bem-sucedido: {result['user']['nome']}")
        print(f"Token: {result['token']['access_token'][:50]}...")
        return result['token']['access_token']
    else:
        print(f"Erro: {response.json()}")
        return None


def test_protected_endpoints(token):
    """Testa endpoints protegidos"""
    if not token:
        print("❌ Token não disponível para testar endpoints protegidos")
        return
    
    print("🛡️ Testando endpoints protegidos...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Testa GET /professor/
    print("\n📋 Listando professores...")
    response = requests.get(f"{BASE_URL}/professor/", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        professors = response.json()
        print(f"Professores encontrados: {len(professors)}")
    else:
        print(f"Erro: {response.json()}")
    
    # Testa POST /professor/
    print("\n➕ Criando novo professor...")
    new_professor = {
        "nome": "Maria Santos",
        "email": "maria@exemplo.com",
        "senha": "654321"
    }
    
    response = requests.post(
        f"{BASE_URL}/professor/",
        json=new_professor,
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Professor criado: {result['nome']} (ID: {result['professor_id']})")
        return result['professor_id']
    else:
        print(f"Erro: {response.json()}")
        return None


def test_unauthorized_access():
    """Testa acesso não autorizado"""
    print("🚫 Testando acesso não autorizado...")
    
    response = requests.get(f"{BASE_URL}/professor/")
    print(f"Status: {response.status_code}")
    print(f"Resposta: {response.json()}\n")


def main():
    """Função principal de teste"""
    print("🚀 Iniciando testes da API SID3D\n")
    
    # Teste de saúde
    test_health()
    
    # Teste de registro
    token = test_register()
    
    # Teste de login
    if not token:
        token = test_login()
    
    # Teste de acesso não autorizado
    test_unauthorized_access()
    
    # Teste de endpoints protegidos
    if token:
        professor_id = test_protected_endpoints(token)
    
    print("✅ Testes concluídos!")


if __name__ == "__main__":
    main() 