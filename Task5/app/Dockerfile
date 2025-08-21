FROM python:3.12-bookworm

# Установка системных пакетов для сборки зависимостей (C++11 и т.п.)
RUN set -eux; \
    export DEBIAN_FRONTEND=noninteractive; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        build-essential \
        curl \
    ; \
    rm -rf /var/lib/apt/lists/*

# Установка рабочей директории
WORKDIR /app

# Копирование файлов зависимостей
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY . .

# Создание пользователя для безопасности
RUN useradd -m -u 1000 raguser && chown -R raguser:raguser /app
USER raguser

# Открытие порта для Streamlit
EXPOSE 8501

# Команда запуска
CMD ["streamlit", "run", "web_interface.py", "--server.port=8501", "--server.address=0.0.0.0"]


