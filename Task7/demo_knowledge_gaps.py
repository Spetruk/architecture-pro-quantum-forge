#!/usr/bin/env python3
"""
Демонстрация анализа пробелов в знаниях без LLM
Показывает только поиск в векторной базе и логирование
"""

import sys
import time
from pathlib import Path
from query_logger import QueryLogger

# Добавляем путь к оригинальному RAG-боту
sys.path.append('./app')

try:
    from rag_bot import RAGConfig
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_chroma import Chroma
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("💡 Установите необходимые зависимости:")
    print("pip install langchain-huggingface langchain-chroma")
    sys.exit(1)

class KnowledgeGapAnalyzer:
    """Анализатор пробелов в знаниях (только поиск, без LLM)"""
    
    def __init__(self, enable_logging: bool = True, log_format: str = "csv"):
        """Инициализация анализатора"""
        print("🔍 Инициализация анализатора пробелов в знаниях...")
        
        # Конфигурация
        self.config = RAGConfig()
        
        # Embeddings модель
        self.embeddings = HuggingFaceEmbeddings(
            model_name=self.config.embedding_model,
            model_kwargs={'device': 'cpu'}
        )
        
        # Векторная БД
        self.vector_db = Chroma(
            persist_directory=self.config.vector_db_path,
            embedding_function=self.embeddings
        )
        
        # Логгер
        self.logger = QueryLogger(log_format=log_format) if enable_logging else None
        
        print("✅ Инициализация завершена")
    
    def search_knowledge(self, query: str, k: int = 5) -> dict:
        """
        Поиск информации в базе знаний
        
        Args:
            query: Поисковый запрос
            k: Количество результатов
            
        Returns:
            Информация о результатах поиска
        """
        start_time = time.time()
        
        try:
            # Поиск в векторной БД
            results = self.vector_db.similarity_search_with_score(query, k=k)
            
            chunks_found = len(results)
            sources = []
            similarity_scores = []
            
            for doc, score in results:
                if hasattr(doc, 'metadata') and doc.metadata:
                    source = doc.metadata.get('source', 'unknown')
                    sources.append(source)
                
                # ChromaDB возвращает расстояния, конвертируем в схожесть
                similarity = 1.0 - score if score <= 1.0 else 0.0
                similarity_scores.append(round(similarity, 3))
            
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Создаем mock-ответ на основе найденных чанков
            if chunks_found > 0:
                mock_response = f"Найдена информация в {chunks_found} источниках: {', '.join(sources[:2])}..."
                if similarity_scores[0] < 0.3:  # Низкая схожесть
                    mock_response = "Информация найдена, но может быть неточной."
            else:
                mock_response = "Извините, я не могу найти информацию по вашему запросу."
            
            # Логирование
            log_data = None
            if self.logger:
                log_data = self.logger.log_query(
                    query_text=query,
                    chunks_found=chunks_found,
                    response_text=mock_response,
                    sources=sources,
                    similarity_scores=similarity_scores,
                    response_time_ms=response_time_ms
                )
            
            return {
                'query': query,
                'chunks_found': chunks_found,
                'sources': sources,
                'similarity_scores': similarity_scores,
                'response': mock_response,
                'success': log_data['response_successful'] if log_data else chunks_found > 0,
                'response_time_ms': response_time_ms
            }
            
        except Exception as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Логирование ошибки
            if self.logger:
                self.logger.log_query(
                    query_text=query,
                    chunks_found=0,
                    response_text="",
                    response_time_ms=response_time_ms,
                    error_message=str(e)
                )
            
            return {
                'query': query,
                'chunks_found': 0,
                'sources': [],
                'similarity_scores': [],
                'response': f"Ошибка: {str(e)}",
                'success': False,
                'response_time_ms': response_time_ms,
                'error': str(e)
            }
    
    def test_knowledge_gaps(self):
        """Тестирование пробелов в знаниях"""
        
        print("\n🧪 ТЕСТИРОВАНИЕ ПРОБЕЛОВ В ЗНАНИЯХ")
        print("="*50)
        
        # Тестовые запросы
        test_queries = [
            # Удаленные сущности (должны быть пробелами)
            "Что такое Void Core?",
            "Расскажи о персонаже Xarn Velgor",
            "Объясни технологию Synth Flux",
            
            # Существующие сущности (должны находиться)
            "Кто такой Arin Solara?",
            "Что такое Lumen Blade?", 
            "Расскажи о планете Elyndar",
            "Кто такой Kade Rhaul?",
            "Что такое Aeon Raptor?",
            
            # Общие вопросы
            "Какие технологии существуют?",
            "Кто главные персонажи?"
        ]
        
        results = {
            'total_queries': len(test_queries),
            'successful': 0,
            'failed': 0,
            'gaps': [],
            'known': [],
            'details': []
        }
        
        print(f"📋 Всего тестовых запросов: {len(test_queries)}")
        print()
        
        for i, query in enumerate(test_queries, 1):
            print(f"🔍 Тест {i}/{len(test_queries)}: {query}")
            
            result = self.search_knowledge(query)
            
            # Анализ результата
            chunks_found = result['chunks_found']
            success = result['success']
            
            if success:
                results['successful'] += 1
                results['known'].append(query)
                status = "✅ НАЙДЕНО"
                details = f"чанков: {chunks_found}, схожесть: {result['similarity_scores'][0] if result['similarity_scores'] else 0:.3f}"
            else:
                results['failed'] += 1
                results['gaps'].append(query)
                status = "❌ ПРОБЕЛ"
                details = f"чанков: {chunks_found}"
            
            print(f"   {status} ({details})")
            
            # Показываем источники для успешных запросов
            if success and result['sources']:
                print(f"   📂 Источники: {', '.join(result['sources'][:2])}...")
            
            results['details'].append(result)
            print()
        
        # Итоговая статистика
        success_rate = (results['successful'] / results['total_queries']) * 100
        
        print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
        print(f"   Всего запросов: {results['total_queries']}")
        print(f"   Успешных: {results['successful']}")
        print(f"   Пробелов: {results['failed']}")
        print(f"   Процент покрытия: {success_rate:.1f}%")
        print()
        
        # Выявленные пробелы
        if results['gaps']:
            print("🚨 ОБНАРУЖЕННЫЕ ПРОБЕЛЫ В ЗНАНИЯХ:")
            for i, gap in enumerate(results['gaps'], 1):
                print(f"   {i}. {gap}")
            print()
        
        # Известная информация
        if results['known']:
            print("✅ ИЗВЕСТНАЯ ИНФОРМАЦИЯ:")
            for i, known in enumerate(results['known'], 1):
                print(f"   {i}. {known}")
            print()
        
        return results
    
    def get_analytics(self):
        """Получение аналитики"""
        return self.logger.get_analytics()

def main():
    """Основная функция"""
    try:
        # Создание анализатора
        analyzer = KnowledgeGapAnalyzer()
        
        # Тестирование пробелов
        test_results = analyzer.test_knowledge_gaps()
        
        # Аналитика
        print("📈 АНАЛИТИКА ЛОГОВ:")
        analytics = analyzer.get_analytics()
        
        for key, value in analytics.items():
            if key != 'recent_failed_queries':
                print(f"   {key}: {value}")
        
        # Недавние неуспешные запросы
        if analytics.get('recent_failed_queries'):
            print("\n🚨 НЕУСПЕШНЫЕ ЗАПРОСЫ (выявляют пробелы):")
            for failed in analytics['recent_failed_queries']:
                print(f"   - {failed['query']} ({failed['timestamp'][:19]})")
        
        print("\n✅ Анализ завершен! Логи сохранены в logs/query_logs/")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
