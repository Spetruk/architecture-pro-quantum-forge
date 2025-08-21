#!/usr/bin/env python3
"""
ДЕМО: Результаты тестирования "золотого набора" 
Показывает, как выглядели бы результаты при рабочем API
"""

import json
from datetime import datetime
from pathlib import Path

def create_demo_results():
    """Создание демонстрационных результатов тестирования"""
    
    # Симуляция результатов успешного тестирования
    demo_results = {
        "metadata": {
            "test_id": "demo_123",
            "timestamp": datetime.now().isoformat(),
            "technique": "base",
            "total_time": 12.5,
            "questions_count": 13
        },
        "statistics": {
            "overall_accuracy": 0.846,  # 11/13
            "total_questions": 13,
            "correct_answers": 11,
            "success_questions": {
                "total": 8,
                "correct": 8,  # Все известные темы отвечены верно
                "accuracy": 1.0
            },
            "failure_questions": {
                "total": 5,
                "correct": 3,  # 3 из 5 неизвестных тем корректно отклонены
                "accuracy": 0.6
            },
            "average_completeness": 0.823,
            "categories": {
                "characters": {"total": 2, "correct": 2, "accuracy": 1.0},
                "technologies": {"total": 2, "correct": 2, "accuracy": 1.0},
                "locations": {"total": 2, "correct": 2, "accuracy": 1.0},
                "events": {"total": 2, "correct": 2, "accuracy": 1.0},
                "removed_entities": {"total": 3, "correct": 3, "accuracy": 1.0},
                "external_knowledge": {"total": 2, "correct": 0, "accuracy": 0.0}
            }
        },
        "detailed_results": [
            # Успешные ответы на известные темы
            {
                "question_id": "known_01",
                "question": "Кто такой Arin Solara?",
                "category": "characters",
                "expected_type": "success",
                "response": "Arin Solara - это опытный исследователь и член экспедиционной команды. Он известен своими исследованиями в области космических технологий и участием в ключевых миссиях.",
                "evaluation": {
                    "correct": True,
                    "completeness": 0.95,
                    "is_refusal": False,
                    "keyword_coverage": 0.8,
                    "chunks_found": 5
                }
            },
            {
                "question_id": "known_02",
                "question": "Что такое Lumen Blade?",
                "category": "technologies",
                "expected_type": "success",
                "response": "Lumen Blade - это передовая энергетическая технология, используемая в качестве оружия. Она создает лезвие из чистой энергии, способное прорезать большинство материалов.",
                "evaluation": {
                    "correct": True,
                    "completeness": 0.88,
                    "is_refusal": False,
                    "keyword_coverage": 0.75,
                    "chunks_found": 4
                }
            },
            # Корректные отказы на удаленные сущности
            {
                "question_id": "unknown_01",
                "question": "Кто такой Xarn Velgor?",
                "category": "removed_entities",
                "expected_type": "failure",
                "response": "Информация о Xarn Velgor не найдена в базе знаний.",
                "evaluation": {
                    "correct": True,
                    "completeness": 1.0,
                    "is_refusal": True,
                    "keyword_coverage": 1.0,
                    "chunks_found": 0
                }
            },
            {
                "question_id": "unknown_02",
                "question": "Что такое Synth Flux?",
                "category": "removed_entities",
                "expected_type": "failure",
                "response": "Информация о Synth Flux не найдена в базе знаний.",
                "evaluation": {
                    "correct": True,
                    "completeness": 1.0,
                    "is_refusal": True,
                    "keyword_coverage": 1.0,
                    "chunks_found": 0
                }
            },
            # Неправильный ответ (галлюцинация)
            {
                "question_id": "unknown_04",
                "question": "Кто такой Darth Vader?",
                "category": "external_knowledge",
                "expected_type": "failure",
                "response": "Darth Vader - это могущественный темный лорд, известный своими способностями к управлению силой и черной броней.",
                "evaluation": {
                    "correct": False,  # Галлюцинация - должен был отказаться
                    "completeness": 0.0,
                    "is_refusal": False,
                    "keyword_coverage": 0.0,
                    "chunks_found": 3
                }
            }
        ]
    }
    
    return demo_results

def print_analysis():
    """Вывод анализа результатов тестирования"""
    
    results = create_demo_results()
    stats = results["statistics"]
    
    print("🎯 АНАЛИЗ РЕЗУЛЬТАТОВ «ЗОЛОТОГО НАБОРА»")
    print("="*60)
    
    print(f"\n📊 ОБЩАЯ СТАТИСТИКА:")
    print(f"  Общая точность: {stats['overall_accuracy']:.1%}")
    print(f"  Всего вопросов: {stats['total_questions']}")
    print(f"  Корректных ответов: {stats['correct_answers']}")
    
    print(f"\n✅ ИЗВЕСТНЫЕ ТЕМЫ (должны отвечать):")
    success_stats = stats['success_questions']
    print(f"  Точность: {success_stats['accuracy']:.1%}")
    print(f"  Результат: {success_stats['correct']}/{success_stats['total']}")
    
    print(f"\n❌ НЕИЗВЕСТНЫЕ ТЕМЫ (должны отказываться):")
    failure_stats = stats['failure_questions']
    print(f"  Точность: {failure_stats['accuracy']:.1%}")
    print(f"  Результат: {failure_stats['correct']}/{failure_stats['total']}")
    
    print(f"\n📂 ПО КАТЕГОРИЯМ:")
    for category, cat_stats in stats['categories'].items():
        status = "✅" if cat_stats['accuracy'] >= 0.8 else "⚠️" if cat_stats['accuracy'] >= 0.5 else "❌"
        print(f"  {status} {category}: {cat_stats['accuracy']:.1%} ({cat_stats['correct']}/{cat_stats['total']})")
    
    print(f"\n🔍 ПРОБЛЕМЫ И НАХОДКИ:")
    
    # Анализ результатов
    if stats['success_questions']['accuracy'] == 1.0:
        print("  ✅ Отлично отвечает на известные темы")
    else:
        print("  ⚠️  Проблемы с ответами на известные темы")
    
    if stats['failure_questions']['accuracy'] >= 0.8:
        print("  ✅ Хорошо распознает неизвестные темы")
    elif stats['failure_questions']['accuracy'] >= 0.5:
        print("  ⚠️  Частично распознает неизвестные темы")
    else:
        print("  ❌ Плохо распознает неизвестные темы (риск галлюцинаций)")
    
    # Анализ по категориям
    categories = stats['categories']
    if categories['removed_entities']['accuracy'] == 1.0:
        print("  ✅ Корректно обрабатывает удаленные сущности")
    else:
        print("  ❌ Проблемы с удаленными сущностями (база знаний неполная)")
    
    if categories['external_knowledge']['accuracy'] < 0.5:
        print("  ⚠️  Использует внешние знания (риск галлюцинаций)")
    
    print(f"\n💡 РЕКОМЕНДАЦИИ:")
    
    if stats['overall_accuracy'] >= 0.9:
        print("  🎉 Отличное качество! Система готова к продакшену")
    elif stats['overall_accuracy'] >= 0.8:
        print("  👍 Хорошее качество, незначительные улучшения")
    elif stats['overall_accuracy'] >= 0.7:
        print("  ⚠️  Требуются улучшения промптов")
    else:
        print("  🔧 Требуется серьезная доработка системы")
    
    # Специфичные рекомендации
    if failure_stats['accuracy'] < 0.8:
        print("  🔧 Улучшить промпты для обработки неизвестных тем")
        print("  🔧 Добавить больше паттернов для распознавания пробелов")
    
    if categories['external_knowledge']['accuracy'] < 0.8:
        print("  🔧 Усилить инструкции 'НЕ использовать внешние знания'")
    
    print(f"\n📈 СЛЕДУЮЩИЕ ШАГИ:")
    print("  1. Расширить золотой набор до 50+ вопросов")
    print("  2. Добавить автоматический мониторинг качества")
    print("  3. Настроить алерты при снижении точности")
    print("  4. Регулярно обновлять тестовый набор")

if __name__ == "__main__":
    print_analysis()
    
    # Сохранение демо результатов
    demo_results = create_demo_results()
    
    results_dir = Path("test_results")
    results_dir.mkdir(exist_ok=True)
    
    demo_file = results_dir / "golden_set_demo_results.json"
    with open(demo_file, 'w', encoding='utf-8') as f:
        json.dump(demo_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Демо-результаты сохранены: {demo_file}")
