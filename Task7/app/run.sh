#!/bin/bash

# Скрипт для запуска RAG-бота в Docker

set -e

echo "🚀 Запуск RAG-бота в Docker..."

# Останавливаем существующие контейнеры
echo "🛑 Остановка существующих контейнеров..."
docker-compose down

# Собираем и запускаем
echo "🔨 Сборка Docker образа..."
docker-compose build

echo "🚀 Запуск RAG-бота..."
docker-compose up

# Ждем запуска
echo "⏳ Ожидание запуска сервиса..."
sleep 10

# Проверяем статус
if docker-compose ps | grep -q "Up"; then
    echo "✅ RAG-бот успешно запущен!"
    echo "🌐 Веб-интерфейс доступен по адресу: http://localhost:8501"
    echo ""
    echo "📋 Полезные команды:"
    echo "  docker-compose logs -f    # Просмотр логов"
    echo "  docker-compose down       # Остановка"
    echo "  docker-compose restart    # Перезапуск"
else
    echo "❌ Ошибка запуска. Проверьте логи:"
    docker-compose logs
    exit 1
fi
