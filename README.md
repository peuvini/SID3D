# SID3D - Sistema de Impressão 3D

Sistema de autenticação completo para o projeto SID3D com JWT e hash seguro de senhas.

## 🚀 Funcionalidades

- **Autenticação JWT**: Sistema seguro de tokens
- **Hash de Senhas**: Senhas criptografadas com bcrypt
- **Proteção de Rotas**: Middleware para proteger endpoints
- **CRUD de Professores**: Gerenciamento completo de professores
- **Validação de Dados**: Schemas Pydantic para validação

## 📋 Pré-requisitos

- Python 3.8+
- PostgreSQL (ou outro banco configurado no Prisma)
- pip

## 🛠️ Instalação

1. **Clone o repositório**:
```bash
git clone <seu-repositorio>
cd SID3D
```

2. **Instale as dependências**:
```bash
pip install -r requirements.txt
```

3. **Configure o banco de dados**:
```bash
# Configure a variável DATABASE_URL no seu ambiente
export DATABASE_URL="postgresql://usuario:senha@localhost:5432/sid3d"

# Gere o cliente Prisma
prisma generate
```

4. **Execute as migrações**:
```bash
prisma db push
```

## 🚀 Executando o Projeto

```bash
uvicorn app.main:app --reload
```

A API estará disponível em: `http://localhost:8000`

## 📚 Documentação da API

Acesse a documentação interativa em: `http://localhost:8000/docs`

## 🔐 Endpoints de Autenticação

### Registro
```http
POST /auth/register
Content-Type: application/json

{
  "nome": "João Silva",
  "email": "joao@exemplo.com",
  "senha": "senha123"
}
```

### Login
```http
POST /auth/login
Content-Type: application/json

{
  "email": "joao@exemplo.com",
  "senha": "senha123"
}
```

### Verificar Usuário Atual
```http
GET /auth/me
Authorization: Bearer <seu-token-jwt>
```

## 👨‍🏫 Endpoints de Professores (Protegidos)

Todos os endpoints de professores requerem autenticação:

```http
GET /professor/          # Listar todos os professores
GET /professor/{id}      # Buscar professor por ID
POST /professor/         # Criar novo professor
PUT /professor/{id}      # Atualizar professor
DELETE /professor/{id}   # Deletar professor
```

**Headers necessários**:
```
Authorization: Bearer <seu-token-jwt>
```

## 🔧 Configuração de Produção

1. **Altere a chave secreta** em `app/auth/auth_service.py`:
```python
self.secret_key = "sua_chave_secreta_muito_segura_aqui"
```

2. **Configure variáveis de ambiente**:
```bash
export SECRET_KEY="sua_chave_secreta_muito_segura_aqui"
export DATABASE_URL="postgresql://usuario:senha@localhost:5432/sid3d"
```

3. **Configure CORS** em `main.py` para seus domínios específicos.

## 📁 Estrutura do Projeto

```
SID3D/
├── app/
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── auth_controller.py
│   │   ├── auth_middleware.py
│   │   ├── auth_schemas.py
│   │   └── auth_service.py
│   └── professor/
│       ├── __init__.py
│       ├── controller.py
│       ├── repository.py
│       ├── schemas.py
│       └── service.py
├── prisma/
│   └── schema.prisma
├── main.py
├── requirements.txt
└── README.md
```

## 🔒 Segurança

- **Senhas**: Hash com bcrypt
- **Tokens**: JWT com expiração
- **Validação**: Schemas Pydantic
- **Proteção**: Middleware de autenticação

## 🧪 Testando

1. **Registre um usuário**:
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"nome": "Teste", "email": "teste@exemplo.com", "senha": "123456"}'
```

2. **Faça login**:
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "teste@exemplo.com", "senha": "123456"}'
```

3. **Use o token para acessar rotas protegidas**:
```bash
curl -X GET "http://localhost:8000/professor/" \
  -H "Authorization: Bearer <seu-token-aqui>"
```

## 📝 Licença

Este projeto está sob a licença MIT. 