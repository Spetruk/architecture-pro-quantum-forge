#!/usr/bin/env python3
"""
Скрипт для тестирования поиска по векторному индексу
"""

import json
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

def load_vectorstore():
    """Загружает сохраненный векторный индекс"""
    embeddings = HuggingFaceEmbeddings(
        model_name="all-mpnet-base-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    vectorstore = Chroma(
        persist_directory="./chroma_db",
        embedding_function=embeddings
    )
    
    return vectorstore

def test_queries(vectorstore):
    """Тестирует различные запросы"""
    test_cases = [
        {
            "query": "Кто такой Xarn Velgor?",
            "description": "Поиск информации о главном персонаже"
        },
        {
            "query": "Что такое Synth Flux?",
            "description": "Поиск определения ключевого понятия"
        },
        {
            "query": "Расскажи о битве на Krael",
            "description": "Поиск информации о конкретном событии"
        },
        {
            "query": "Какие технологии используют Wardens?",
            "description": "Поиск технологической информации"
        },
        {
            "query": "Где находится Aurelia Prime?",
            "description": "Поиск географической информации"
        },
        {
            "query": "Как работает Lumen Blade?",
            "description": "Поиск технических деталей"
        },
        {
            "query": "Кто такие Wardens?",
            "description": "Поиск определения организации"
        },
        {
            "query": "Что произошло в Echo Wars?",
            "description": "Поиск исторической информации"
        }
    ]
    
    print("🧪 ТЕСТИРОВАНИЕ ПОИСКА ПО ВЕКТОРНОМУ ИНДЕКСУ")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['description']}")
        print(f"   Запрос: '{test_case['query']}'")
        print("-" * 40)
        
        # Выполняем поиск
        results = vectorstore.similarity_search(test_case['query'], k=3)
        
        for j, result in enumerate(results, 1):
            print(f"   {j}. Источник: {result.metadata['source']}")
            print(f"      Категория: {result.metadata['category']}")
            print(f"      Чанк: {result.metadata['chunk_id']}")
            print(f"      Размер чанка: {len(result.page_content)} символов")
            print(f"      Позиция: {result.metadata.get('chunk_index', 'N/A')} из {result.metadata.get('total_chunks', 'N/A')}")
            print(f"      Текст:")
            print(f"      {result.page_content}")
            print()

def main():
    """Основная функция"""
    try:
        # Загружаем векторный индекс
        print("📂 Загрузка векторного индекса...")
        vectorstore = load_vectorstore()
        print("✅ Векторный индекс загружен")
        
        # Тестируем поиск
        test_queries(vectorstore)
        
        # Показываем статистику индекса
        print("\n📊 СТАТИСТИКА ИНДЕКСА:")
        print(f"   Всего документов в индексе: {vectorstore._collection.count()}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        print("Убедитесь, что векторный индекс был создан с помощью build_index.py")

if __name__ == "__main__":
    main()
