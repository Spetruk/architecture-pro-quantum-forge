#!/usr/bin/env python3
"""
Система логирования запросов для RAG-бота
Отслеживает каждый запрос для анализа покрытия базы знаний
"""

import json
import csv
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import re

class QueryLogger:
    """Логгер запросов к RAG-боту"""
    
    def __init__(self, log_format="sqlite", log_path="logs/query_logs"):
        """
        Инициализация логгера
        
        Args:
            log_format: Формат логов ("sqlite", "csv", "jsonl")
            log_path: Путь к файлам логов
        """
        self.log_format = log_format
        self.log_path = Path(log_path)
        self.log_path.mkdir(parents=True, exist_ok=True)
        
        # Инициализация хранилища логов
        if log_format == "sqlite":
            self._init_sqlite()
        elif log_format == "csv":
            self._init_csv()
        elif log_format == "jsonl":
            self.jsonl_file = self.log_path / "queries.jsonl"
    
    def _init_sqlite(self):
        """Инициализация SQLite базы данных"""
        self.db_path = self.log_path / "queries.db"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                query_text TEXT NOT NULL,
                chunks_found INTEGER NOT NULL,
                chunks_used INTEGER DEFAULT 0,
                response_length INTEGER NOT NULL,
                response_successful BOOLEAN NOT NULL,
                sources TEXT,
                similarity_scores TEXT,
                response_time_ms INTEGER DEFAULT 0,
                error_message TEXT,
                session_id TEXT,
                user_feedback TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _init_csv(self):
        """Инициализация CSV файла"""
        self.csv_file = self.log_path / "queries.csv"
        
        # Создаем заголовки если файл не существует
        if not self.csv_file.exists():
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp', 'query_text', 'chunks_found', 'chunks_used',
                    'response_length', 'response_successful', 'sources',
                    'similarity_scores', 'response_time_ms', 'error_message',
                    'session_id', 'user_feedback'
                ])
    
    def log_query(self, 
                  query_text: str,
                  chunks_found: int,
                  response_text: str,
                  sources: List[str] = None,
                  similarity_scores: List[float] = None,
                  response_time_ms: int = 0,
                  error_message: str = None,
                  session_id: str = None,
                  user_feedback: str = None) -> Dict[str, Any]:
        """
        Логирование запроса
        
        Args:
            query_text: Текст запроса пользователя
            chunks_found: Количество найденных чанков
            response_text: Текст ответа бота
            sources: Список источников (файлов)
            similarity_scores: Оценки схожести найденных чанков
            response_time_ms: Время ответа в миллисекундах
            error_message: Сообщение об ошибке (если есть)
            session_id: Идентификатор сессии
            user_feedback: Обратная связь от пользователя
            
        Returns:
            Dict с логируемыми данными
        """
        timestamp = datetime.now().isoformat()
        response_length = len(response_text) if response_text else 0
        response_successful = self._evaluate_response_success(
            query_text, response_text, chunks_found, error_message
        )
        chunks_used = min(chunks_found, 5)  # Обычно используется максимум 5 чанков
        
        # Подготовка данных для логирования
        log_data = {
            'timestamp': timestamp,
            'query_text': query_text,
            'chunks_found': chunks_found,
            'chunks_used': chunks_used,
            'response_length': response_length,
            'response_successful': response_successful,
            'sources': json.dumps(sources or []),
            'similarity_scores': json.dumps(similarity_scores or []),
            'response_time_ms': response_time_ms,
            'error_message': error_message,
            'session_id': session_id,
            'user_feedback': user_feedback
        }
        
        # Запись в выбранный формат
        if self.log_format == "sqlite":
            self._log_to_sqlite(log_data)
        elif self.log_format == "csv":
            self._log_to_csv(log_data)
        elif self.log_format == "jsonl":
            self._log_to_jsonl(log_data)
        
        return log_data
    
    def _evaluate_response_success(self, query: str, response: str, 
                                 chunks_found: int, error: str) -> bool:
        """
        Оценка успешности ответа на основе эвристик
        
        Args:
            query: Текст запроса
            response: Текст ответа
            chunks_found: Количество найденных чанков
            error: Сообщение об ошибке
            
        Returns:
            True если ответ считается успешным
        """
        if error:
            return False
        
        if not response or len(response.strip()) < 20:
            return False
        
        if chunks_found == 0:
            return False
        
        # Проверка на стандартные фразы о незнании
        failure_patterns = [
            r"я не знаю",
            r"не могу найти",
            r"нет информации",
            r"не имею данных",
            r"к сожалению",
            r"извините",
            r"недостаточно информации",
            r"не упоминается в предоставленной информации",
            r"не упоминается в базе знаний", 
            r"не упоминается в данном контексте",
            r"не упоминается в документах",
            r"не представлена в данных документах",
            r"конкретная информация.*не представлена",
            r"информация.*не представлена",
            r"термин.*не упоминается",
            r"понятие.*не упоминается",
            r"информация.*отсутствует",
            r"нет данных о",
            r"не найдено упоминаний",
            r"может быть упомянут.*но.*информация.*не представлена",
            r"информация.*не найдена в базе знаний",
            r"не найдена в базе знаний"
        ]
        
        response_lower = response.lower()
        for pattern in failure_patterns:
            if re.search(pattern, response_lower):
                return False
        
        # Если найдены чанки и ответ не слишком короткий - успешный
        if chunks_found > 0 and len(response) > 30:
            return True
        
        return False
    
    def _log_to_sqlite(self, data: Dict[str, Any]):
        """Запись в SQLite"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO query_logs 
            (timestamp, query_text, chunks_found, chunks_used, response_length,
             response_successful, sources, similarity_scores, response_time_ms,
             error_message, session_id, user_feedback)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['timestamp'], data['query_text'], data['chunks_found'],
            data['chunks_used'], data['response_length'], data['response_successful'],
            data['sources'], data['similarity_scores'], data['response_time_ms'],
            data['error_message'], data['session_id'], data['user_feedback']
        ))
        
        conn.commit()
        conn.close()
    
    def _log_to_csv(self, data: Dict[str, Any]):
        """Запись в CSV"""
        with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                data['timestamp'], data['query_text'], data['chunks_found'],
                data['chunks_used'], data['response_length'], data['response_successful'],
                data['sources'], data['similarity_scores'], data['response_time_ms'],
                data['error_message'], data['session_id'], data['user_feedback']
            ])
    
    def _log_to_jsonl(self, data: Dict[str, Any]):
        """Запись в JSONL"""
        with open(self.jsonl_file, 'a', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
            f.write('\n')
    
    def get_analytics(self) -> Dict[str, Any]:
        """
        Получение аналитики по логам
        
        Returns:
            Словарь с аналитическими данными
        """
        if self.log_format != "sqlite":
            return {"error": "Аналитика доступна только для SQLite формата"}
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Общая статистика
        cursor.execute("SELECT COUNT(*) FROM query_logs")
        total_queries = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM query_logs WHERE response_successful = 1")
        successful_queries = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(response_time_ms) FROM query_logs WHERE response_time_ms > 0")
        avg_response_time = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT AVG(chunks_found) FROM query_logs")
        avg_chunks_found = cursor.fetchone()[0] or 0
        
        # Неуспешные запросы (для выявления пробелов)
        cursor.execute("""
            SELECT query_text, timestamp 
            FROM query_logs 
            WHERE response_successful = 0 
            ORDER BY timestamp DESC 
            LIMIT 10
        """)
        failed_queries = cursor.fetchall()
        
        conn.close()
        
        success_rate = (successful_queries / total_queries * 100) if total_queries > 0 else 0
        
        return {
            "total_queries": total_queries,
            "successful_queries": successful_queries,
            "success_rate": round(success_rate, 2),
            "avg_response_time_ms": round(avg_response_time, 2),
            "avg_chunks_found": round(avg_chunks_found, 2),
            "recent_failed_queries": [
                {"query": q[0], "timestamp": q[1]} for q in failed_queries
            ]
        }

# Пример использования
if __name__ == "__main__":
    # Тестирование логгера
    logger = QueryLogger(log_format="sqlite")
    
    # Тест успешного запроса
    logger.log_query(
        query_text="Расскажи о персонаже Arin Solara",
        chunks_found=3,
        response_text="Arin Solara - это опытный исследователь...",
        sources=["characters/Arin Solara.txt"],
        similarity_scores=[0.85, 0.73, 0.68],
        response_time_ms=250
    )
    
    # Тест неуспешного запроса (пробел в знаниях)
    logger.log_query(
        query_text="Что такое Void Core?",
        chunks_found=0,
        response_text="Извините, я не могу найти информацию о Void Core.",
        sources=[],
        similarity_scores=[],
        response_time_ms=150
    )
    
    # Получение аналитики
    analytics = logger.get_analytics()
    print("📊 Аналитика запросов:")
    print(json.dumps(analytics, indent=2, ensure_ascii=False))
