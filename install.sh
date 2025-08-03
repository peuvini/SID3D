#!/bin/bash

echo "🚀 Instalando dependências do SID3D..."

# Verifica se o Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Por favor, instale o Python 3.8+"
    exit 1
fi

# Verifica a versão do Python
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "🐍 Versão do Python: $PYTHON_VERSION"

# Cria ambiente virtual se não existir
if [ ! -d "venv" ]; then
    echo "📦 Criando ambiente virtual..."
    python3 -m venv venv
fi

# Ativa o ambiente virtual
echo "🔧 Ativando ambiente virtual..."
source venv/bin/activate

# Atualiza pip
echo "⬆️ Atualizando pip..."
pip install --upgrade pip

# Tenta instalar com versões específicas primeiro
echo "📥 Instalando dependências principais..."
pip install fastapi==0.109.0 uvicorn[standard]==0.27.0

# Instala pydantic separadamente para evitar conflitos
echo "📥 Instalando Pydantic..."
pip install "pydantic[email]>=2.6.0"

# Instala as demais dependências
echo "📥 Instalando demais dependências..."
pip install prisma==0.12.0 python-jose[cryptography]==3.3.0 passlib[bcrypt]==1.7.4 python-multipart==0.0.6 bcrypt==4.1.2 PyJWT==2.8.0 requests==2.31.0

# Verifica se a instalação foi bem-sucedida
if [ $? -eq 0 ]; then
    echo "✅ Instalação concluída com sucesso!"
    echo ""
    echo "🎯 Para executar o projeto:"
    echo "   source venv/bin/activate"
    echo "   python run.py"
    echo ""
    echo "📚 Para acessar a documentação:"
    echo "   http://localhost:8000/docs"
else
    echo "❌ Erro na instalação. Tentando abordagem alternativa..."
    
    # Tenta com versões mais recentes
    echo "🔄 Tentando com versões mais recentes..."
    pip install --upgrade fastapi uvicorn pydantic prisma python-jose passlib python-multipart bcrypt PyJWT requests
    
    if [ $? -eq 0 ]; then
        echo "✅ Instalação alternativa concluída!"
    else
        echo "❌ Falha na instalação. Verifique os logs acima."
        exit 1
    fi
fi

echo ""
echo "🔧 Configurando Prisma..."
prisma generate

echo ""
echo "🎉 Setup concluído! Execute 'python run.py' para iniciar o servidor." 