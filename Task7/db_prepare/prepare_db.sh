#!/bin/bash
#
# Универсальный скрипт подготовки базы данных для анализа RAG-системы
# Создает искусственные пробелы в знаниях и пересоздает векторный индекс
#

set -e  # Остановка при ошибке

echo "🚀 ПОДГОТОВКА БАЗЫ ДАННЫХ ДЛЯ АНАЛИЗА ПРОБЕЛОВ"
echo "=============================================="

# Переход в корневую папку проекта
cd "$(dirname "$0")/.."

echo "📍 Рабочая папка: $(pwd)"
echo

# Этап 1: Создание пробелов в знаниях
echo "🔥 Этап 1: Создание искусственных пробелов в базе знаний..."
echo "   Удаляем ключевые сущности: Void Core, Xarn Velgor, Synth Flux"
echo

# Физическое удаление файлов сущностей
echo "🗑️  Удаление файлов целевых сущностей..."
entities_deleted=0

if [ -f "knowledge_base/locations/Void Core.txt" ]; then
    rm "knowledge_base/locations/Void Core.txt"
    echo "   ✅ Удален: Void Core.txt"
    entities_deleted=$((entities_deleted + 1))
fi

if [ -f "knowledge_base/characters/Xarn Velgor.txt" ]; then
    rm "knowledge_base/characters/Xarn Velgor.txt"
    echo "   ✅ Удален: Xarn Velgor.txt"
    entities_deleted=$((entities_deleted + 1))
fi

if [ -f "knowledge_base/technologies/Synth Flux.txt" ]; then
    rm "knowledge_base/technologies/Synth Flux.txt"
    echo "   ✅ Удален: Synth Flux.txt"
    entities_deleted=$((entities_deleted + 1))
fi

echo "   📊 Удалено файлов: $entities_deleted"
echo

# Удаление упоминаний из других файлов
echo "🔧 Удаление упоминаний из других файлов..."
if [ -f "db_prepare/remove_entity_mentions.py" ]; then
    python3 db_prepare/remove_entity_mentions.py
    echo "✅ Упоминания удалены из связанных файлов"
else
    echo "❌ Файл remove_entity_mentions.py не найден!"
    exit 1
fi

echo "✅ Пробелы в знаниях созданы"

echo

# Этап 2: Очистка старого индекса
echo "🗑️  Этап 2: Очистка старого векторного индекса..."
if [ -d "chroma_db" ]; then
    rm -rf chroma_db
    echo "✅ Старый индекс удален"
else
    echo "⚠️  Старый индекс не найден (это нормально)"
fi

echo

# Этап 3: Создание нового индекса
echo "🔍 Этап 3: Создание нового векторного индекса..."
echo "   Индексируем базу знаний с созданными пробелами..."
echo

if [ -f "db_prepare/build_index.py" ]; then
    python3 db_prepare/build_index.py
    echo "✅ Новый векторный индекс создан"
else
    echo "❌ Файл build_index.py не найден!"
    exit 1
fi

echo

# Этап 4: Проверка результатов
echo "📊 Этап 4: Проверка результатов..."

if [ -f "db_prepare/removed_entities.txt" ]; then
    echo "📝 Удаленные сущности:"
    cat db_prepare/removed_entities.txt | sed 's/^/   - /'
else
    echo "⚠️  Файл removed_entities.txt не найден"
fi

echo

if [ -d "chroma_db" ]; then
    echo "✅ Векторный индекс готов к использованию"
else
    echo "❌ Векторный индекс не создан!"
    exit 1
fi

if [ -f "indexing_stats.json" ]; then
    echo "📈 Статистика индексации:"
    python3 -c "
import json
try:
    with open('indexing_stats.json', 'r', encoding='utf-8') as f:
        stats = json.load(f)
    print(f'   Документов: {stats.get(\"total_documents\", \"N/A\")}')
    print(f'   Чанков: {stats.get(\"total_chunks\", \"N/A\")}')
    print(f'   База знаний: {stats.get(\"knowledge_base_path\", \"N/A\")}')
except:
    print('   Не удалось прочитать статистику')
"
fi

echo
echo "🎯 ПОДГОТОВКА ЗАВЕРШЕНА!"
echo "=============================================="
echo "✅ База данных готова для анализа пробелов"
echo "🧪 Теперь можно запускать скрипты анализа:"
echo "   - python3 demo_knowledge_gaps.py"
echo "   - python3 coverage_analyzer.py" 
echo "   - python3 comprehensive_analysis.py"
echo
