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
RUN prisma generate
RUN prisma db push
EXPOSE 8000
CMD ["python3", "run.py"]
