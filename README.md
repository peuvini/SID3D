# SID3D - Sistema de Impressão 3D

Sistema completo para autenticação, gerenciamento de professores e manipulação de arquivos 3D, com integração AWS S3 e banco de dados PostgreSQL.

## 🚀 Funcionalidades

- Autenticação JWT segura
- Hash de senhas com bcrypt
- Proteção de rotas via middleware
- CRUD de professores
- Manipulação e conversão de arquivos 3D
- Upload e download de arquivos via AWS S3
- Gerenciamento de imagens DICOM
- Validação de dados com Pydantic

## 📋 Pré-requisitos

- Python 3.8+
- PostgreSQL
- pip

## 🛠️ Instalação

1. **Clone o repositório**:
   ```bash
   git clone https://github.com/peuvini/SID3D.git
   cd SID3D
   ```

2. **Instale as dependências**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure as variáveis de ambiente**  
   Crie um arquivo `.env` na raiz do projeto com o seguinte conteúdo (preencha os valores conforme sua configuração):

   ```env
   DATABASE_URL=postgresql://<usuario>:<senha>@localhost:5432/sid_3d
   SECRET_KEY=<sua_chave_secreta>
   JWT_ALGORITHM=HS256
   JWT_EXPIRE_MINUTES=30
   HOST=0.0.0.0
   PORT=8080
   DEBUG=true
   ALLOWED_ORIGINS=*
   AWS_ACCESS_KEY_ID=<sua_access_key>
   AWS_SECRET_ACCESS_KEY=<sua_secret_access_key>
   S3_BUCKET_NAME=<nome_do_bucket>
   AWS_REGION=<regiao_aws>
   ```

   > **Atenção:** Não compartilhe suas credenciais reais em ambientes públicos.

4. **Configure o banco de dados**:
   ```bash
   prisma generate
   prisma db push
   ```

## 🚀 Executando o Projeto

```bash
uvicorn app.main:app --reload
```

A API estará disponível em: `http://localhost:8080`

## 📚 Documentação da API

Acesse a documentação interativa em: `http://localhost:8080/docs`

## 🔐 Endpoints de Autenticação

- **Registro:** `POST /auth/register`
- **Login:** `POST /auth/login`
- **Verificar usuário:** `GET /auth/me` (requer JWT)

## 👨‍🏫 Endpoints de Professores

- `GET /professor/` — Listar todos
- `GET /professor/{id}` — Buscar por ID
- `POST /professor/` — Criar novo
- `PUT /professor/{id}` — Atualizar
- `DELETE /professor/{id}` — Deletar

**Headers necessários:**  
`Authorization: Bearer <seu-token-jwt>`

## 📁 Estrutura do Projeto

```
SID3D/
├── .env
├── .gitignore
├── config.py
├── debug.log
├── DICOM_PREVIEW_UPDATE.md
├── docker-compose.yml
├── Dockerfile
├── install.sh
├── README.md
├── requirements-dev.txt
├── requirements.txt
├── run.py
├── test_api.py
├── test_imports.py
├── __pycache__/
├── app/
│   ├── dependencies.py
│   ├── main.py
│   ├── __pycache__/
│   ├── arquivo3D/
│   │   ├── background_processor.py
│   │   ├── controller.py
│   │   ├── conversion_job_repository.py
│   │   ├── factory.py
│   │   ├── repository.py
│   │   ├── schemas.py
│   │   ├── service.py
│   │   └── __pycache__/
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── auth_controller.py
│   │   ├── auth_middleware.py
│   │   ├── auth_schemas.py
│   │   ├── auth_service.py
│   │   └── __pycache__/
│   ├── dicom/
│   │   ├── controller.py
│   │   ├── repository.py
│   │   ├── schemas.py
│   │   ├── service.py
│   │   └── __pycache__/
│   ├── impressora/
│   │   ├── controller.py
│   │   ├── repository.py
│   │   ├── schemas.py
│   │   ├── service.py
│   ├── professor/
│   │   ├── __init__.py
│   │   ├── controller.py
│   │   ├── repository.py
│   │   ├── schemas.py
│   │   ├── service.py
│   │   └── __pycache__/
│   └── utils/
│       ├── dicom_processor.py
│       ├── mesh_generator.py
│       └── __pycache__/
├── prisma/
│   ├── schema.prisma
│   └── migrations/
│       ├── migration_lock.toml
│       ├── 20250103120000_add_dicom_image_preview/
│       │   └── migration.sql
│       └── 20250803183613_add_autoincrement_ids/
│           └── migration.sql
└── tests/
    ├── conftest.py
    ├── test_arquivo3D_controller.py
    ├── test_arquivo3d_service.py
    ├── test_dicom_controller.py
    ├── test_dicom_service.py
    ├── test_professor_controller.py
    └── test_professor_service.py
```

## 🔒 Segurança

- Senhas com hash bcrypt
- Tokens JWT com expiração
- Validação de dados com Pydantic
- Middleware de autenticação

## 🧪 Testando

1. **Registre um usuário**:
   ```bash
   curl -X POST "http://localhost:8080/auth/register" \
     -H "Content-Type: application/json" \
     -d '{"nome": "Teste", "email": "teste@exemplo.com", "senha": "123456"}'
   ```

2. **Faça login**:
   ```bash
   curl -X POST "http://localhost:8080/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"email": "teste@exemplo.com", "senha": "123456"}'
   ```

3. **Use o token para acessar rotas protegidas**:
   ```bash
   curl -X GET "http://localhost:8080/professor/" \
     -H "Authorization: Bearer <seu-token-aqui>"
   ```

## 📝 Licença

Este projeto está sob a licença MIT.
