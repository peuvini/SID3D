FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    openssl \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Variáveis de ambiente para produção
ARG DATABASE_URL
ENV DATABASE_URL=${DATABASE_URL}
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Configurações para HTTPS e produção
ENV RAILWAY_ENVIRONMENT=production
ENV FORCE_HTTPS=true

# Copiar código da aplicação
COPY . .

# Gerar cliente Prisma
RUN prisma generate

# Não executar db push no build - deixar para o runtime
# RUN prisma db push

# Criar usuário não-root para segurança
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser:appuser /app
USER appuser

# Expor porta
EXPOSE 8000

# Comando de inicialização com migração
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
