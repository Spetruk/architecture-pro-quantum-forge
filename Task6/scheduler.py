#!/usr/bin/env python3
"""
Планировщик для автоматического обновления индекса
Поддерживает различные режимы запуска: cron, интервальный, ручной
"""

import os
import sys
import time
import signal
import threading
from datetime import datetime, timedelta
from pathlib import Path
import yaml
import subprocess
import logging

# Добавляем текущую директорию в путь
sys.path.append(str(Path(__file__).parent))


class UpdateScheduler:
    """Планировщик автоматических обновлений"""
    
    def __init__(self, config_path: str = "auto_update_config.yaml"):
        self.script_dir = Path(__file__).parent
        self.config_path = self.script_dir / config_path
        self.config = self._load_config()
        self.logger = self._setup_logging()
        self.running = False
        self.thread = None
        
    def _load_config(self):
        """Загрузка конфигурации"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Конфигурация не найдена: {self.config_path}")
            
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _setup_logging(self):
        """Настройка логирования для планировщика"""
        log_config = self.config.get('logging', {})
        log_level = getattr(logging, log_config.get('level', 'INFO'))
        
        logger = logging.getLogger('UpdateScheduler')
        logger.setLevel(log_level)
        logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        return logger
    
    def run_update_script(self):
        """Запуск скрипта обновления"""
        script_path = self.script_dir / "update_index.py"
        
        try:
            self.logger.info("Запуск скрипта обновления...")
            
            # Запуск скрипта в подпроцессе
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=str(self.script_dir),
                capture_output=True,
                text=True,
                timeout=3600  # 1 час таймаут
            )
            
            if result.returncode == 0:
                self.logger.info("Скрипт обновления выполнен успешно")
            else:
                self.logger.error(f"Ошибка выполнения скрипта: код {result.returncode}")
                self.logger.error(f"Stderr: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            self.logger.error("Таймаут выполнения скрипта обновления")
        except Exception as e:
            self.logger.error(f"Ошибка запуска скрипта: {e}")
    
    def interval_worker(self):
        """Рабочий поток для интервального запуска"""
        interval_minutes = self.config.get('scheduler', {}).get('interval_minutes', 60)
        interval_seconds = interval_minutes * 60
        
        self.logger.info(f"Запуск интервального планировщика (каждые {interval_minutes} мин)")
        
        while self.running:
            try:
                # Запуск обновления
                self.run_update_script()
                
                # Ожидание следующего интервала
                self.logger.info(f"Ожидание {interval_minutes} минут до следующего обновления...")
                
                for _ in range(interval_seconds):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                self.logger.error(f"Ошибка в планировщике: {e}")
                time.sleep(60)  # Пауза при ошибке
    
    def start_interval_mode(self):
        """Запуск в интервальном режиме"""
        if self.running:
            self.logger.warning("Планировщик уже запущен")
            return
            
        self.running = True
        self.thread = threading.Thread(target=self.interval_worker, daemon=True)
        self.thread.start()
        
        self.logger.info("Планировщик запущен в интервальном режиме")
        
        # Обработка сигналов для корректного завершения
        def signal_handler(signum, frame):
            self.logger.info("Получен сигнал завершения...")
            self.stop()
            sys.exit(0)
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Ожидание завершения
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Остановка планировщика"""
        if self.running:
            self.logger.info("Остановка планировщика...")
            self.running = False
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=5)
            self.logger.info("Планировщик остановлен")
    
    def generate_cron_entry(self) -> str:
        """Генерация записи для cron"""
        cron_config = self.config.get('scheduler', {})
        cron_expression = cron_config.get('cron_expression', '0 6 * * *')  # Каждый день в 6:00
        
        script_path = self.script_dir / "update_index.py"
        log_file = self.script_dir / "logs" / "cron.log"
        
        cron_entry = f"{cron_expression} cd {self.script_dir} && {sys.executable} {script_path} >> {log_file} 2>&1"
        
        return cron_entry
    
    def install_cron(self):
        """Установка задачи в cron (только для Unix-систем)"""
        if os.name != 'posix':
            self.logger.error("Cron поддерживается только на Unix-системах")
            return False
            
        try:
            cron_entry = self.generate_cron_entry()
            
            # Получение текущих cron задач
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            current_crontab = result.stdout if result.returncode == 0 else ""
            
            # Проверка, что задача еще не добавлена
            if "update_index.py" in current_crontab:
                self.logger.info("Задача уже добавлена в cron")
                return True
            
            # Добавление новой задачи
            new_crontab = current_crontab + f"\n# Auto-update RAG index\n{cron_entry}\n"
            
            # Установка обновленного cron
            process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
            process.communicate(input=new_crontab)
            
            if process.returncode == 0:
                self.logger.info("Задача успешно добавлена в cron")
                self.logger.info(f"Cron entry: {cron_entry}")
                return True
            else:
                self.logger.error("Ошибка добавления задачи в cron")
                return False
                
        except Exception as e:
            self.logger.error(f"Ошибка установки cron: {e}")
            return False
    
    def remove_cron(self):
        """Удаление задачи из cron"""
        if os.name != 'posix':
            self.logger.error("Cron поддерживается только на Unix-системах")
            return False
            
        try:
            # Получение текущих cron задач
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            if result.returncode != 0:
                self.logger.info("Cron задачи не найдены")
                return True
                
            current_crontab = result.stdout
            
            # Фильтрация строк, не связанных с update_index.py
            lines = current_crontab.split('\n')
            filtered_lines = []
            skip_next = False
            
            for line in lines:
                if "Auto-update RAG index" in line:
                    skip_next = True
                elif skip_next and "update_index.py" in line:
                    skip_next = False
                elif not ("update_index.py" in line):
                    filtered_lines.append(line)
            
            new_crontab = '\n'.join(filtered_lines)
            
            # Установка обновленного cron
            process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
            process.communicate(input=new_crontab)
            
            if process.returncode == 0:
                self.logger.info("Задача удалена из cron")
                return True
            else:
                self.logger.error("Ошибка удаления задачи из cron")
                return False
                
        except Exception as e:
            self.logger.error(f"Ошибка удаления из cron: {e}")
            return False


def main():
    """Основная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Планировщик автоматического обновления RAG индекса')
    parser.add_argument('command', choices=['run-once', 'start-interval', 'install-cron', 'remove-cron', 'show-cron'],
                      help='Команда для выполнения')
    
    args = parser.parse_args()
    
    scheduler = UpdateScheduler()
    
    if args.command == 'run-once':
        print("Запуск разового обновления...")
        scheduler.run_update_script()
        
    elif args.command == 'start-interval':
        print("Запуск в интервальном режиме...")
        scheduler.start_interval_mode()
        
    elif args.command == 'install-cron':
        print("Установка задачи в cron...")
        success = scheduler.install_cron()
        sys.exit(0 if success else 1)
        
    elif args.command == 'remove-cron':
        print("Удаление задачи из cron...")
        success = scheduler.remove_cron()
        sys.exit(0 if success else 1)
        
    elif args.command == 'show-cron':
        print("Предлагаемая запись для cron:")
        print(scheduler.generate_cron_entry())


if __name__ == "__main__":
    main()
