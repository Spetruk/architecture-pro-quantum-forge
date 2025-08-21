#!/usr/bin/env python3
"""
Упрощенная система автоматического обновления векторного индекса
Работает с базовыми модулями Python и интегрируется с существующим build_index.py
"""

import os
import sys
import time
import hashlib
import logging
import json
import yaml
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple


class SimpleAutoUpdateManager:
    """Упрощенный менеджер автоматического обновления векторного индекса"""
    
    def __init__(self, config_path: str = "auto_update_config.yaml"):
        self.config_path = Path(config_path)
        self.script_dir = Path(__file__).parent
        self.config = self._load_config()
        self.logger = self._setup_logging()
        self.processed_files_cache = self._load_processed_files()
    
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
            # Создаем базовую конфигурацию если файл не найден
            default_config = {
                'data_sources': {
                    'local_folders': [
                        {
                            'path': './data_sources/incoming',
                            'enabled': True,
                            'watch_extensions': ['.txt', '.md']
                        }
                    ]
                },
                'processing': {
                    'chunk_size': 2000,
                    'chunk_overlap': 200,
                    'min_chunk_size': 10
                },
                'logging': {
                    'level': 'INFO',
                    'log_file': './logs/auto_update.log'
                }
            }
            return default_config
            
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception:
            # Если не удается загрузить YAML, возвращаем базовую конфигурацию
            return {
                'data_sources': {
                    'local_folders': [
                        {
                            'path': './data_sources/incoming',
                            'enabled': True,
                            'watch_extensions': ['.txt', '.md']
                        }
                    ]
                },
                'logging': {
                    'level': 'INFO',
                    'log_file': './logs/auto_update.log'
                }
            }
    
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
        logger = logging.getLogger('SimpleAutoUpdateManager')
        logger.setLevel(log_level)
        logger.handlers.clear()
        
        # File handler
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        return logger
    
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
    
    def copy_files_to_knowledge_base(self, new_files: List[Tuple[Path, str]]) -> int:
        """Копирование новых файлов в knowledge_base для обработки существующим build_index.py"""
        if not new_files:
            return 0
            
        # Определение целевой папки
        kb_incoming = self.script_dir / "knowledge_base" / "incoming"
        kb_incoming.mkdir(parents=True, exist_ok=True)
        
        copied_count = 0
        
        for file_path, file_hash in new_files:
            try:
                # Чтение и проверка содержимого
                content = file_path.read_text(encoding='utf-8', errors='ignore').strip()
                
                if not content:
                    self.logger.warning(f"Файл пуст: {file_path}")
                    continue
                
                # Копирование файла в knowledge_base
                dest_file = kb_incoming / file_path.name
                dest_file.write_text(content, encoding='utf-8')
                
                # Обновление кэша
                file_key = str(file_path.relative_to(self.script_dir))
                self.processed_files_cache[file_key] = file_hash
                
                copied_count += 1
                self.logger.info(f"Скопирован файл: {self._get_relative_path(file_path)} -> {self._get_relative_path(dest_file)}")
                
            except Exception as e:
                self.logger.error(f"Ошибка обработки файла {self._get_relative_path(file_path)}: {e}")
        
        return copied_count
    
    def run_build_index(self) -> bool:
        """Запуск существующего скрипта build_index.py"""
        script_path = self.script_dir / "build_index.py"
        
        if not script_path.exists():
            self.logger.error(f"Скрипт build_index.py не найден: {script_path}")
            return False
        
        try:
            self.logger.info("Запуск build_index.py для обновления индекса...")
            
            # Запуск скрипта в подпроцессе
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=str(self.script_dir),
                capture_output=True,
                text=True,
                timeout=1800  # 30 минут таймаут
            )
            
            if result.returncode == 0:
                self.logger.info("Индекс успешно обновлен")
                # Логируем вывод скрипта
                if result.stdout:
                    for line in result.stdout.split('\n'):
                        if line.strip():
                            self.logger.info(f"build_index: {line.strip()}")
                return True
            else:
                self.logger.error(f"Ошибка выполнения build_index.py: код {result.returncode}")
                if result.stderr:
                    for line in result.stderr.split('\n'):
                        if line.strip():
                            self.logger.error(f"build_index error: {line.strip()}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("Таймаут выполнения build_index.py")
            return False
        except Exception as e:
            self.logger.error(f"Ошибка запуска build_index.py: {e}")
            return False
    
    def run_update(self) -> Dict[str, Any]:
        """Основной цикл обновления"""
        start_time = time.time()
        self.logger.info("=" * 60)
        self.logger.info("ЗАПУСК УПРОЩЕННОГО АВТОМАТИЧЕСКОГО ОБНОВЛЕНИЯ ИНДЕКСА")
        self.logger.info("=" * 60)
        
        stats = {
            "start_time": datetime.now().isoformat(),
            "files_processed": 0,
            "files_copied": 0,
            "index_updated": False,
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
                
                # Копирование файлов в knowledge_base
                copied_count = self.copy_files_to_knowledge_base(new_files)
                stats["files_copied"] = copied_count
                stats["files_processed"] = len(new_files)
                
                for file_path, _ in new_files:
                    stats["new_files"].append({
                        "path": str(file_path.relative_to(self.script_dir))
                    })
                
                if copied_count > 0:
                    # Запуск обновления индекса
                    self.logger.info("Обновление векторного индекса...")
                    index_success = self.run_build_index()
                    stats["index_updated"] = index_success
                    
                    if not index_success:
                        stats["errors"] += 1
                else:
                    self.logger.warning("Не удалось скопировать ни одного файла")
                    stats["errors"] += 1
                
                # Сохранение кэша
                self._save_processed_files()
            
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
        self.logger.info(f"  Найдено новых файлов: {stats['files_processed']}")
        self.logger.info(f"  Скопировано файлов: {stats['files_copied']}")
        self.logger.info(f"  Индекс обновлен: {'Да' if stats['index_updated'] else 'Нет'}")
        self.logger.info(f"  Ошибок: {stats['errors']}")
        self.logger.info("=" * 60)
        
        return stats


def main():
    """Основная функция"""
    try:
        # Инициализация менеджера
        manager = SimpleAutoUpdateManager()
        
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
