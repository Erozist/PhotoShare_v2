# Базовий образ Python 3.11
FROM python:3.11-slim

# Встановлення залежностей системи
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Встановлення pip
RUN pip install --upgrade pip

# Встановлення робочої директорії
WORKDIR /app

# Копіювання файлів проекту
COPY . .

# Копіювання файлу .env
COPY .env .env

# Встановлення залежностей з requirements.txt
RUN pip install -r requirements.txt

# Виставлення порту
EXPOSE 8000

# Команда для запуску FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
