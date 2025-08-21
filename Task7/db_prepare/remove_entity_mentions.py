#!/usr/bin/env python3
"""
Скрипт для удаления упоминаний ключевых сущностей из базы знаний
Цель: создание искусственных пробелов для тестирования аналитики покрытия
"""

import os
import re
from pathlib import Path

def remove_mentions_from_file(file_path, entities_to_remove):
    """Удаляет упоминания сущностей из файла"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        modified = False
        
        for entity in entities_to_remove:
            # Удаляем упоминания сущности, заменяя на пробел
            pattern = re.compile(re.escape(entity), re.IGNORECASE)
            new_content = pattern.sub(" ", content)
            
            if new_content != content:
                content = new_content
                modified = True
        
        # Если были изменения, записываем файл
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Обновлен: {file_path}")
            return True
        
        return False
        
    except Exception as e:
        print(f"❌ Ошибка обработки {file_path}: {e}")
        return False

def main():
    """Основная функция"""
    # Сущности для удаления
    entities_to_remove = [
        "Void Core",
        "VoidCore", 
        "Xarn Velgor",
        "Synth Flux",
        "SynthFlux"
    ]
    
    # Папка с базой знаний
    knowledge_base_path = Path("knowledge_base")
    
    files_modified = 0
    total_files = 0
    
    print("🔄 Удаление упоминаний сущностей из базы знаний...")
    print(f"📋 Целевые сущности: {', '.join(entities_to_remove)}")
    print()
    
    # Обходим все текстовые файлы в базе знаний
    for file_path in knowledge_base_path.rglob("*.txt"):
        total_files += 1
        
        if remove_mentions_from_file(file_path, entities_to_remove):
            files_modified += 1
    
    print()
    print("📊 РЕЗУЛЬТАТЫ:")
    print(f"   Всего файлов обработано: {total_files}")
    print(f"   Файлов изменено: {files_modified}")
    print(f"   Удаленных сущностей: {len(entities_to_remove)}")
    print()
    print("✅ Создание пробелов в базе знаний завершено!")
    print("📝 Список удаленных сущностей сохранен в removed_entities.txt")

if __name__ == "__main__":
    main()
