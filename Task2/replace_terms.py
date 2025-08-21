#!/usr/bin/env python3
import json
import os
import re
import sys

def load_terms_map(terms_path):
    """Загружает словарь соответствий из JSON файла"""
    with open(terms_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_plural_variants(terms_map):
    """Генерирует варианты множественного числа для терминов"""
    plural_terms = {}
    
    for key, value in terms_map.items():
        # Добавляем оригинальный ключ
        plural_terms[key] = value
        
        # Генерируем множественное число
        if key.endswith('y'):
            # Слова на -y: y -> ies
            plural_key = key[:-1] + 'ies'
            plural_value = value[:-1] + 'ies' if value.endswith('y') else value + 's'
            plural_terms[plural_key] = plural_value
        elif key.endswith(('s', 'sh', 'ch', 'x', 'z')):
            # Слова на s, sh, ch, x, z: добавляем -es
            plural_key = key + 'es'
            plural_value = value + 'es'
            plural_terms[plural_key] = plural_value
        else:
            # Обычные слова: добавляем -s
            plural_key = key + 's'
            plural_value = value + 's'
            plural_terms[plural_key] = plural_value
    
    return plural_terms

def generate_case_variants(terms_map):
    """Генерирует варианты терминов с разным регистром"""
    expanded_terms = {}
    
    for key, value in terms_map.items():
        # Добавляем оригинальный ключ
        expanded_terms[key] = value
        
        # Генерируем варианты с разным регистром
        if key.isupper():
            # Если все заглавные, добавляем вариант с первой заглавной
            expanded_terms[key.title()] = value
            expanded_terms[key.lower()] = value.lower()
        elif key.istitle():
            # Если с заглавной буквы, добавляем варианты
            expanded_terms[key.lower()] = value.lower()
            expanded_terms[key.upper()] = value.upper()
        elif key.islower():
            # Если все строчные, добавляем варианты
            expanded_terms[key.title()] = value
            expanded_terms[key.upper()] = value.upper()
        else:
            # Смешанный регистр - добавляем варианты
            expanded_terms[key.lower()] = value.lower()
            expanded_terms[key.upper()] = value.upper()
            expanded_terms[key.title()] = value
    
    return expanded_terms

def replace_terms_in_content(content, terms_map):
    """Заменяет термины в содержимом файла"""
    # Генерируем варианты с множественным числом
    plural_terms = generate_plural_variants(terms_map)
    
    # Генерируем варианты с разным регистром
    expanded_terms = generate_case_variants(plural_terms)
    
    # Сортируем ключи по длине (от длинных к коротким) чтобы избежать частичных замен
    keys = sorted(expanded_terms.keys(), key=lambda k: len(k), reverse=True)
    
    for key in keys:
        value = expanded_terms[key]
        # Используем более агрессивную замену без word boundaries для всех терминов
        pattern = re.compile(re.escape(key), re.IGNORECASE)
        content = pattern.sub(value, content)
    
    return content

def replace_terms_in_filename(filename, terms_map):
    """Заменяет термины в имени файла"""
    name, ext = os.path.splitext(filename)
    
    # Генерируем варианты с множественным числом
    plural_terms = generate_plural_variants(terms_map)
    
    # Генерируем варианты с разным регистром
    expanded_terms = generate_case_variants(plural_terms)
    
    # Сортируем ключи по длине (от длинных к коротким)
    keys = sorted(expanded_terms.keys(), key=lambda k: len(k), reverse=True)
    
    for key in keys:
        value = expanded_terms[key]
        # Для имен файлов используем простую замену
        pattern = re.compile(re.escape(key))
        name = pattern.sub(value, name)
    
    return name + ext

def process_directory(root_dir, terms_map):
    """Обрабатывает все файлы в директории и поддиректориях"""
    processed_files = 0
    renamed_files = 0
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Обрабатываем содержимое файлов
        for filename in filenames:
            if not filename.lower().endswith('.txt'):
                continue
                
            filepath = os.path.join(dirpath, filename)
            
            try:
                # Читаем файл
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Заменяем термины в содержимом
                new_content = replace_terms_in_content(content, terms_map)
                
                # Записываем обратно, если что-то изменилось
                if new_content != content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    processed_files += 1
                    print(f"Обработан: {filepath}")
                    
            except Exception as e:
                print(f"Ошибка при обработке {filepath}: {e}")
        
        # Переименовываем файлы
        for filename in list(filenames):
            if not filename.lower().endswith('.txt'):
                continue
                
            old_path = os.path.join(dirpath, filename)
            new_filename = replace_terms_in_filename(filename, terms_map)
            
            if new_filename != filename:
                new_path = os.path.join(dirpath, new_filename)
                
                # Обрабатываем конфликты имен
                counter = 1
                while os.path.exists(new_path):
                    name, ext = os.path.splitext(new_filename)
                    new_path = os.path.join(dirpath, f"{name}_{counter}{ext}")
                    counter += 1
                
                try:
                    os.rename(old_path, new_path)
                    renamed_files += 1
                    print(f"Переименован: {filename} → {os.path.basename(new_path)}")
                except Exception as e:
                    print(f"Ошибка при переименовании {old_path}: {e}")
    
    return processed_files, renamed_files

def main():
    root_dir = "knowledge_base"
    terms_path = "terms_map.json"
    
    if not os.path.exists(root_dir):
        print(f"Директория {root_dir} не найдена!")
        sys.exit(1)
    
    if not os.path.exists(terms_path):
        print(f"Файл {terms_path} не найден!")
        sys.exit(1)
    
    print("Загружаем словарь соответствий...")
    terms_map = load_terms_map(terms_path)
    print(f"Загружено {len(terms_map)} базовых терминов для замены")
    
    # Показываем количество расширенных терминов
    plural_terms = generate_plural_variants(terms_map)
    expanded_terms = generate_case_variants(plural_terms)
    print(f"Сгенерировано {len(expanded_terms)} терминов с учетом регистра и множественного числа")
    
    print(f"\nОбрабатываем директорию: {root_dir}")
    processed, renamed = process_directory(root_dir, terms_map)
    
    print(f"\nГотово!")
    print(f"Обработано файлов: {processed}")
    print(f"Переименовано файлов: {renamed}")

if __name__ == "__main__":
    main()
