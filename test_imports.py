#!/usr/bin/env python3
"""
Script para testar se todas as importações estão funcionando
"""

def test_imports():
    """Testa todas as importações necessárias"""
    try:
        print("🔍 Testando importações...")
        
        # Testa importações básicas
        print("✅ Importando FastAPI...")
        from fastapi import FastAPI
        
        print("✅ Importando Pydantic...")
        from pydantic import BaseModel
        
        print("✅ Importando configurações...")
        from config import settings
        
        print("✅ Importando auth service...")
        from app.auth.auth_service import AuthService
        
        print("✅ Importando auth schemas...")
        from app.auth.auth_schemas import LoginRequest, RegisterRequest
        
        print("✅ Importando auth controller...")
        from app.auth.auth_controller import router as auth_router
        
        print("✅ Importando auth middleware...")
        from app.auth.auth_middleware import require_auth
        
        print("✅ Importando professor schemas...")
        from app.professor.schemas import ProfessorCreate, ProfessorResponse
        
        print("✅ Importando professor service...")
        from app.professor.service import ProfessorService
        
        print("✅ Importando professor controller...")
        from app.professor.controller import router as professor_router
        
        print("✅ Importando main app...")
        from app.main import app
        
        print("🎉 Todas as importações funcionaram!")
        # CORREÇÃO: Usamos 'assert True' para indicar sucesso ao pytest.
        assert True
        
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        # CORREÇÃO: Usamos 'assert False' com uma mensagem para indicar falha ao pytest.
        assert False, f"Erro de importação: {e}"
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        # CORREÇÃO: Usamos 'assert False' com uma mensagem para indicar falha ao pytest.
        assert False, f"Erro inesperado: {e}"


if __name__ == "__main__":
    # Esta função é para executar o script diretamente, não via pytest.
    # Ela não precisa de 'assert'.
    def run_check():
        try:
            test_imports()
            # Se o assert não falhou, significa sucesso.
            return True
        except AssertionError:
            return False

    success = run_check()
    if success:
        print("\n🚀 O projeto está pronto para ser executado!")
        print("Execute: python run.py")
    else:
        print("\n❌ Há problemas que precisam ser resolvidos.")