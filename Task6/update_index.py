#!/usr/bin/env python3
"""
Система автоматического обновления векторного индекса
Автоматически сканирует источники данных, обновляет индекс и логирует процесс
"""

import os
import sys
import time
import hashlib
import logging
import json
import yaml
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple
import shutil

# Добавляем текущую директорию в путь для импорта модулей
sys.path.append(str(Path(__file__).parent))

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document


class AutoUpdateManager:
    """Менеджер автоматического обновления векторного индекса"""
    
    def __init__(self, config_path: str = "auto_update_config.yaml"):
        self.config_path = Path(config_path)
        self.script_dir = Path(__file__).parent
        self.config = self._load_config()
        self.logger = self._setup_logging()
        self.processed_files_cache = self._load_processed_files()
        
        # Инициализация компонентов
        self.embeddings = None
        self.vector_db = None
        self.text_splitter = None
        self._initialize_components()
    
    def _get_relative_path(self, file_path: Path) -> str:
        """Получение относительного пути для логирования"""
        try:
            return str(file_path.relative_to(self.script_dir))
        except ValueError:
            # Если файл не в пределах скрипта, возвращаем только имя файла
            return file_path.name
        
    def _load_config(self) -> Dict[str, Any]:
        """Загрузка конфигурации"""
        config_file = self.script_dir / self.config_path
        if not config_file.exists():
            raise FileNotFoundError(f"Конфигурационный файл не найден: {config_file}")
            
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _setup_logging(self) -> logging.Logger:
        """Настройка логирования"""
        log_config = self.config.get('logging', {})
        log_level = getattr(logging, log_config.get('level', 'INFO'))
        
        # Создание папки для логов
        log_file = self.script_dir / log_config.get('log_file', 'logs/auto_update.log')
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Настройка форматера
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Настройка logger
        logger = logging.getLogger('AutoUpdateManager')
        logger.setLevel(log_level)
        logger.handlers.clear()  # Очистка существующих handlers
        
        # File handler с ротацией
        from logging.handlers import RotatingFileHandler
        max_size = log_config.get('max_file_size_mb', 10) * 1024 * 1024
        backup_count = log_config.get('backup_count', 5)
        
        file_handler = RotatingFileHandler(
            log_file, maxBytes=max_size, backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        return logger
    
    def _initialize_components(self):
        """Инициализация компонентов для обработки"""
        processing_config = self.config.get('processing', {})
        
        # Инициализация эмбеддингов
        model_name = processing_config.get('embedding_model', 'all-mpnet-base-v2')
        self.embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Инициализация text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=processing_config.get('chunk_size', 2000),
            chunk_overlap=processing_config.get('chunk_overlap', 200),
            length_function=len,
            separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""]
        )
        
        # Инициализация векторной БД
        db_config = self.config.get('vector_db', {})
        persist_dir = self.script_dir / db_config.get('persist_directory', 'chroma_db')
        
        # Создание БД если не существует
        if not persist_dir.exists():
            self.logger.info(f"Создание новой векторной БД в {persist_dir}")
            persist_dir.mkdir(parents=True, exist_ok=True)
            # Создаем пустую БД
            self.vector_db = Chroma(
                persist_directory=str(persist_dir),
                embedding_function=self.embeddings
            )
        else:
            self.vector_db = Chroma(
                persist_directory=str(persist_dir),
                embedding_function=self.embeddings
            )
            
        self.logger.info("Компоненты инициализированы успешно")
    
    def _load_processed_files(self) -> Dict[str, str]:
        """Загрузка кэша обработанных файлов"""
        cache_file = self.script_dir / "processed_files_cache.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Ошибка загрузки кэша: {e}")
        return {}
    
    def _save_processed_files(self):
        """Сохранение кэша обработанных файлов"""
        cache_file = self.script_dir / "processed_files_cache.json"
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.processed_files_cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Ошибка сохранения кэша: {e}")
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Вычисление хэша файла для отслеживания изменений"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            self.logger.error(f"Ошибка вычисления хэша для {file_path}: {e}")
            return ""
    

    def scan_for_new_files(self) -> List[Tuple[Path, str]]:
        """Сканирование источников на наличие новых или измененных файлов"""
        new_files = []
        
        # Сканирование локальных папок
        local_folders = self.config.get('data_sources', {}).get('local_folders', [])
        for folder_config in local_folders:
            if not folder_config.get('enabled', True):
                continue
                
            folder_path = self.script_dir / folder_config['path']
            if not folder_path.exists():
                self.logger.warning(f"Папка не существует: {folder_path}")
                continue
                
            extensions = folder_config.get('watch_extensions', ['.txt', '.md'])
            
            for ext in extensions:
                for file_path in folder_path.rglob(f"*{ext}"):
                    if file_path.is_file():
                        file_hash = self._calculate_file_hash(file_path)
                        file_key = str(file_path.relative_to(self.script_dir))
                        
                        # Проверка, является ли файл новым или измененным
                        if file_key not in self.processed_files_cache or \
                           self.processed_files_cache[file_key] != file_hash:
                            new_files.append((file_path, file_hash))
                            self.logger.info(f"Найден новый/измененный файл: {self._get_relative_path(file_path)}")
        
        return new_files
    
    def process_file(self, file_path: Path, file_hash: str) -> List[Document]:
        """Обработка отдельного файла"""
        try:
            # Чтение содержимого файла
            content = file_path.read_text(encoding='utf-8', errors='ignore').strip()
            
            if not content:
                self.logger.warning(f"Файл пуст: {self._get_relative_path(file_path)}")
                return []
            
            # Создание метаданных
            relative_path = file_path.relative_to(self.script_dir)
            metadata = {
                "source": str(relative_path),
                "filename": file_path.name,
                "file_path": str(file_path),
                "file_size": len(content),
                "file_hash": file_hash,
                "processed_at": datetime.now().isoformat(),
                "category": relative_path.parts[0] if len(relative_path.parts) > 1 else "root"
            }
            
            # Создание документа
            document = Document(page_content=content, metadata=metadata)
            
            # Разбиение на чанки
            chunks = self.text_splitter.split_documents([document])
            
            # Фильтрация по минимальному размеру
            min_size = self.config.get('processing', {}).get('min_chunk_size', 10)
            filtered_chunks = []
            
            for i, chunk in enumerate(chunks):
                if len(chunk.page_content.strip()) >= min_size:
                    # Обновление метаданных чанка
                    chunk.metadata.update({
                        "chunk_id": f"{file_path.stem}_{i}",
                        "chunk_index": i,
                        "total_chunks": len(chunks)
                    })
                    filtered_chunks.append(chunk)
            
            self.logger.info(f"Обработан файл {self._get_relative_path(file_path)}: {len(filtered_chunks)} чанков")
            return filtered_chunks
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки файла {self._get_relative_path(file_path)}: {e}")
            return []
    
    def update_vector_db(self, new_chunks: List[Document]) -> int:
        """Обновление векторной БД новыми чанками"""
        if not new_chunks:
            return 0
            
        try:
            # Добавление новых чанков в БД
            self.vector_db.add_documents(new_chunks)
            self.logger.info(f"Добавлено {len(new_chunks)} чанков в векторную БД")
            return len(new_chunks)
            
        except Exception as e:
            self.logger.error(f"Ошибка обновления векторной БД: {e}")
            return 0
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Получение статистики индекса"""
        try:
            collection = self.vector_db._collection
            if collection:
                count = collection.count()
                return {
                    "total_documents": count,
                    "last_updated": datetime.now().isoformat()
                }
        except Exception as e:
            self.logger.error(f"Ошибка получения статистики: {e}")
        
        return {"total_documents": "N/A", "last_updated": "N/A"}
    
    def run_update(self) -> Dict[str, Any]:
        """Основной цикл обновления"""
        start_time = time.time()
        self.logger.info("=" * 60)
        self.logger.info("ЗАПУСК АВТОМАТИЧЕСКОГО ОБНОВЛЕНИЯ ИНДЕКСА")
        self.logger.info("=" * 60)
        
        stats = {
            "start_time": datetime.now().isoformat(),
            "files_processed": 0,
            "chunks_added": 0,
            "errors": 0,
            "new_files": [],
            "end_time": None,
            "duration_seconds": 0
        }
        
        try:
            # Сканирование новых файлов
            self.logger.info("Сканирование источников данных...")
            new_files = self.scan_for_new_files()
            
            if not new_files:
                self.logger.info("Новых файлов не найдено")
            else:
                self.logger.info(f"Найдено {len(new_files)} новых/измененных файлов")
                
                all_chunks = []
                
                # Обработка каждого файла
                for file_path, file_hash in new_files:
                    try:
                        chunks = self.process_file(file_path, file_hash)
                        if chunks:
                            all_chunks.extend(chunks)
                            stats["files_processed"] += 1
                            stats["new_files"].append({
                                "path": str(file_path.relative_to(self.script_dir)),
                                "chunks": len(chunks)
                            })
                            
                            # Обновление кэша
                            file_key = str(file_path.relative_to(self.script_dir))
                            self.processed_files_cache[file_key] = file_hash
                            
                    except Exception as e:
                        self.logger.error(f"Ошибка обработки файла {file_path}: {e}")
                        stats["errors"] += 1
                
                # Обновление векторной БД
                if all_chunks:
                    chunks_added = self.update_vector_db(all_chunks)
                    stats["chunks_added"] = chunks_added
                
                # Сохранение кэша
                self._save_processed_files()
            
            # Получение итоговой статистики
            index_stats = self.get_index_stats()
            
        except Exception as e:
            self.logger.error(f"Критическая ошибка при обновлении: {e}")
            stats["errors"] += 1
        
        # Завершение
        end_time = time.time()
        stats["end_time"] = datetime.now().isoformat()
        stats["duration_seconds"] = round(end_time - start_time, 2)
        
        # Итоговый лог
        self.logger.info("=" * 60)
        self.logger.info("РЕЗУЛЬТАТЫ ОБНОВЛЕНИЯ:")
        self.logger.info(f"  Время выполнения: {stats['duration_seconds']} сек")
        self.logger.info(f"  Обработано файлов: {stats['files_processed']}")
        self.logger.info(f"  Добавлено чанков: {stats['chunks_added']}")
        self.logger.info(f"  Ошибок: {stats['errors']}")
        if 'total_documents' in locals():
            self.logger.info(f"  Всего документов в индексе: {index_stats.get('total_documents', 'N/A')}")
        self.logger.info("=" * 60)
        
        return stats


def main():
    """Основная функция"""
    try:
        # Инициализация менеджера
        manager = AutoUpdateManager()
        
        # Запуск обновления
        results = manager.run_update()
        
        # Сохранение результатов в JSON
        results_file = Path(__file__).parent / "logs" / "last_update_results.json"
        results_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Возврат кода ошибки если были проблемы
        if results["errors"] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
