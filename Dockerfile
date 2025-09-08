FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    openssl \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get clean && rm -rf /var/lib/apt/lists/*
ARG DATABASE_URL
ENV DATABASE_URL=${DATABASE_URL}

COPY . .

# Criar arquivo de log com permissões corretas
RUN touch debug.log && chmod 666 debug.log

EXPOSE 8080
CMD ["python", "run.py"]