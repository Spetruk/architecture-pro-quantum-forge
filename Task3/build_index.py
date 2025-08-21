#!/usr/bin/env python3
"""
Скрипт для создания векторного индекса базы знаний
"""

import json
import os
import time
from pathlib import Path
from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

class KnowledgeBaseIndexer:
    def __init__(self, knowledge_base_path: str = "../Task2/knowledge_base"):
        """
        Инициализация индексера
        
        Args:
            knowledge_base_path: Путь к базе знаний
        """
        self.knowledge_base_path = Path(knowledge_base_path)
        self.embeddings_model = "all-mpnet-base-v2"
        self.embeddings = HuggingFaceEmbeddings(
            model_name=self.embeddings_model,
            model_kwargs={'device': 'cpu'},  # Используем CPU для совместимости
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Настройка сплиттера для разбиения на чанки
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,  # ~2000 символов (более крупные чанки)
            chunk_overlap=200,  # Перекрытие для связности
            length_function=len,
            separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""]
        )
        
        self.documents = []
        self.chunks = []
        
    def load_documents(self) -> List[Document]:
        """Загружает все документы из базы знаний"""
        print("📚 Загрузка документов из базы знаний...")
        
        for file_path in self.knowledge_base_path.rglob("*.txt"):
            if file_path.is_file():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                    
                    if content:  # Пропускаем пустые файлы
                        # Создаем метаданные
                        relative_path = file_path.relative_to(self.knowledge_base_path)
                        category = relative_path.parts[0] if len(relative_path.parts) > 1 else "root"
                        
                        metadata = {
                            "source": str(relative_path),
                            "category": category,
                            "filename": file_path.name,
                            "file_path": str(file_path),
                            "file_size": len(content)
                        }
                        
                        # Создаем документ LangChain
                        doc = Document(
                            page_content=content,
                            metadata=metadata
                        )
                        self.documents.append(doc)
                        
                except Exception as e:
                    print(f"⚠️ Ошибка при загрузке {file_path}: {e}")
        
        print(f"✅ Загружено {len(self.documents)} документов")
        return self.documents
    
    def split_documents(self) -> List[Document]:
        """Разбивает документы на чанки"""
        print("✂️ Разбиение документов на чанки...")
        
        for doc in self.documents:
            chunks = self.text_splitter.split_documents([doc])
            
            # Фильтруем слишком маленькие чанки
            filtered_chunks = []
            for i, chunk in enumerate(chunks):
                # Пропускаем чанки меньше 100 символов
                if len(chunk.page_content.strip()) >= 100:
                    chunk.metadata.update({
                        "chunk_id": f"{doc.metadata['filename']}_{i}",
                        "chunk_index": i,
                        "total_chunks": len(chunks)
                    })
                    filtered_chunks.append(chunk)
            
            self.chunks.extend(filtered_chunks)
        
        print(f"✅ Создано {len(self.chunks)} чанков (после фильтрации)")
        return self.chunks
    
    def create_vector_index(self, persist_directory: str = "./chroma_db") -> Chroma:
        """Создает векторный индекс в ChromaDB"""
        print("🔍 Создание векторного индекса...")
        
        # Создаем директорию для ChromaDB
        os.makedirs(persist_directory, exist_ok=True)
        
        # Создаем векторное хранилище и записываем на диск (chromadb>=1.0.* сохраняет автоматически)
        vectorstore = Chroma.from_documents(
            documents=self.chunks,
            embedding=self.embeddings,
            persist_directory=persist_directory
        )
        
        print(f"✅ Векторный индекс создан и сохранен в {persist_directory}")
        return vectorstore
    
    def test_search(self, vectorstore: Chroma, test_queries: List[str] = None):
        """Тестирует поиск по индексу"""
        if test_queries is None:
            test_queries = [
                "Кто такой Xarn Velgor?",
                "Что такое Synth Flux?",
                "Расскажи о битве на Krael",
                "Какие технологии используют Wardens?",
                "Где находится Aurelia Prime?"
            ]
        
        print("\n🧪 Тестирование поиска:")
        print("=" * 50)
        
        for query in test_queries:
            print(f"\n🔍 Запрос: {query}")
            results = vectorstore.similarity_search(query, k=3)
            
            for i, result in enumerate(results, 1):
                print(f"  {i}. {result.metadata['source']}")
                print(f"     {result.page_content[:150]}...")
                print()
    
    def save_statistics(self, vectorstore: Chroma, processing_time: float):
        """Сохраняет статистику индексации"""
        stats = {
            "model": {
                "name": self.embeddings_model,
                "repository": "https://huggingface.co/sentence-transformers/all-mpnet-base-v2",
                "embedding_size": 768
            },
            "knowledge_base": {
                "path": str(self.knowledge_base_path),
                "total_documents": len(self.documents),
                "total_chunks": len(self.chunks)
            },
            "processing": {
                "time_seconds": processing_time,
                "time_minutes": processing_time / 60,
                "chunks_per_second": len(self.chunks) / processing_time
            },
            "vectorstore": {
                "type": "ChromaDB",
                "persist_directory": "./chroma_db"
            }
        }
        
        with open("indexing_stats.json", "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        
        print(f"📊 Статистика сохранена в indexing_stats.json")
        return stats

def main():
    """Основная функция"""
    print("🚀 Запуск создания векторного индекса")
    print("=" * 50)
    
    start_time = time.time()
    
    # Создаем индексер
    indexer = KnowledgeBaseIndexer()
    
    # Загружаем документы
    indexer.load_documents()
    
    # Разбиваем на чанки
    indexer.split_documents()
    
    # Создаем векторный индекс
    vectorstore = indexer.create_vector_index()
    
    # Тестируем поиск
    indexer.test_search(vectorstore)
    
    # Сохраняем статистику
    processing_time = time.time() - start_time
    stats = indexer.save_statistics(vectorstore, processing_time)
    
    # Выводим итоговую статистику
    print("\n" + "=" * 50)
    print("📈 ИТОГОВАЯ СТАТИСТИКА:")
    print(f"   Модель: {stats['model']['name']}")
    print(f"   Размер эмбеддингов: {stats['model']['embedding_size']}")
    print(f"   Документов: {stats['knowledge_base']['total_documents']}")
    print(f"   Чанков: {stats['knowledge_base']['total_chunks']}")
    print(f"   Время обработки: {stats['processing']['time_minutes']:.2f} минут")
    print(f"   Скорость: {stats['processing']['chunks_per_second']:.1f} чанков/сек")
    print("=" * 50)

if __name__ == "__main__":
    main()
