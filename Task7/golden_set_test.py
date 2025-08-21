#!/usr/bin/env python3
"""
Автоматическое тестирование RAG-бота с помощью "золотого набора" вопросов
Оценивает качество ответов на известные и неизвестные темы
"""

import json
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import re

import sys
sys.path.append('app')
from dotenv import load_dotenv
from rag_bot import RAGBot, RAGConfig

# Загрузка переменных окружения
load_dotenv('app/.env')


class GoldenSetTester:
    """Тестировщик RAG-бота с золотым набором вопросов"""
    
    def __init__(self, config: RAGConfig):
        self.config = config
        self.bot = RAGBot(config, enable_logging=False)  # Отключаем стандартное логирование
        self.test_id = str(uuid.uuid4())[:8]
        
        # Золотой набор вопросов
        self.golden_questions = self._create_golden_set()
        
    def _create_golden_set(self) -> List[Dict[str, Any]]:
        """Создание золотого набора вопросов"""
        
        return [
            # === ВОПРОСЫ НА ИЗВЕСТНЫЕ ТЕМЫ (должны быть корректные ответы) ===
            {
                "id": "known_01",
                "question": "Кто такой Arin Solara?",
                "category": "characters",
                "expected_type": "success",
                "expected_keywords": ["arin solara", "исследователь", "персонаж"],
                "description": "Основной персонаж, должна быть подробная информация"
            },
            {
                "id": "known_02", 
                "question": "Что такое Lumen Blade?",
                "category": "technologies",
                "expected_type": "success",
                "expected_keywords": ["lumen blade", "технология", "оружие"],
                "description": "Технология из базы знаний"
            },
            {
                "id": "known_03",
                "question": "Расскажи про Krael",
                "category": "locations",
                "expected_type": "success", 
                "expected_keywords": ["krael", "место", "локация"],
                "description": "Локация из базы знаний"
            },
            {
                "id": "known_04",
                "question": "Что произошло во время Echo Wars?",
                "category": "events",
                "expected_type": "success",
                "expected_keywords": ["echo wars", "война", "событие"],
                "description": "Важное событие в истории"
            },
            {
                "id": "known_05",
                "question": "Кто такой Eldar Voss?",
                "category": "characters",
                "expected_type": "success",
                "expected_keywords": ["eldar voss", "персонаж"],
                "description": "Персонаж из базы знаний"
            },
            {
                "id": "known_06",
                "question": "Что такое Rift Engine?",
                "category": "technologies", 
                "expected_type": "success",
                "expected_keywords": ["rift engine", "двигатель", "технология"],
                "description": "Технология из базы знаний"
            },
            {
                "id": "known_07",
                "question": "Расскажи про Aurelia Prime",
                "category": "locations",
                "expected_type": "success",
                "expected_keywords": ["aurelia prime", "планета", "место"],
                "description": "Планета из базы знаний"
            },
            {
                "id": "known_08",
                "question": "Что такое Siege of Krael?",
                "category": "events",
                "expected_type": "success", 
                "expected_keywords": ["siege", "krael", "осада"],
                "description": "Событие из базы знаний"
            },
            
            # === ВОПРОСЫ НА УДАЛЕННЫЕ/ОТСУТСТВУЮЩИЕ ТЕМЫ (должны быть отказы) ===
            {
                "id": "unknown_01",
                "question": "Кто такой Xarn Velgor?",
                "category": "removed_entities",
                "expected_type": "failure",
                "expected_keywords": ["не найдена", "не упоминается", "отсутствует"],
                "description": "Удаленная сущность - должен отказаться отвечать"
            },
            {
                "id": "unknown_02", 
                "question": "Что такое Synth Flux?",
                "category": "removed_entities",
                "expected_type": "failure",
                "expected_keywords": ["не найдена", "не упоминается", "отсутствует"],
                "description": "Удаленная сущность - должен отказаться отвечать"
            },
            {
                "id": "unknown_03",
                "question": "Что такое Void Core?", 
                "category": "removed_entities",
                "expected_type": "failure",
                "expected_keywords": ["не найдена", "не упоминается", "отсутствует"],
                "description": "Удаленная сущность - должен отказаться отвечать"
            },
            {
                "id": "unknown_04",
                "question": "Кто такой Darth Vader?",
                "category": "external_knowledge",
                "expected_type": "failure", 
                "expected_keywords": ["не найдена", "не упоминается", "отсутствует"],
                "description": "Внешние знания - должен отказаться отвечать"
            },
            {
                "id": "unknown_05",
                "question": "Что такое Death Star?",
                "category": "external_knowledge",
                "expected_type": "failure",
                "expected_keywords": ["не найдена", "не упоминается", "отсутствует"],
                "description": "Внешние знания - должен отказаться отвечать"
            }
        ]
    
    def _evaluate_response(self, question_data: Dict[str, Any], response: str, 
                          chunks_found: int) -> Dict[str, Any]:
        """Оценка качества ответа"""
        
        expected_type = question_data["expected_type"]
        expected_keywords = question_data["expected_keywords"]
        response_lower = response.lower()
        
        # Проверка на паттерны отказа
        failure_patterns = [
            r"не найдена в базе знаний",
            r"не упоминается в.*информации",
            r"не упоминается в.*контексте", 
            r"не упоминается в.*документах",
            r"информация.*не найдена",
            r"информация.*отсутствует",
            r"нет информации",
            r"не могу найти"
        ]
        
        is_refusal = any(re.search(pattern, response_lower) for pattern in failure_patterns)
        
        # Проверка наличия ожидаемых ключевых слов
        keyword_matches = sum(1 for keyword in expected_keywords 
                            if keyword.lower() in response_lower)
        keyword_coverage = keyword_matches / len(expected_keywords) if expected_keywords else 0
        
        # Оценка корректности
        if expected_type == "success":
            # Для успешных ответов: не должно быть отказа и должны быть ключевые слова
            is_correct = not is_refusal and keyword_coverage > 0.3 and chunks_found > 0
            completeness = min(keyword_coverage, 1.0)
        else:
            # Для неудачных ответов: должен быть отказ
            is_correct = is_refusal
            completeness = 1.0 if is_refusal else 0.0
        
        return {
            "correct": is_correct,
            "completeness": completeness,
            "is_refusal": is_refusal,
            "keyword_coverage": keyword_coverage,
            "keyword_matches": keyword_matches,
            "chunks_found": chunks_found,
            "response_length": len(response)
        }
    
    def run_test(self, technique: str = "base") -> Dict[str, Any]:
        """Запуск полного тестирования"""
        
        print(f"🧪 Запуск тестирования RAG-бота (техника: {technique})")
        print(f"📊 Тестовый набор: {len(self.golden_questions)} вопросов")
        print("-" * 60)
        
        results = []
        start_time = time.time()
        
        for i, question_data in enumerate(self.golden_questions, 1):
            print(f"[{i:2d}/{len(self.golden_questions)}] {question_data['question']}")
            
            # Получение ответа от бота
            bot_response = self.bot.generate_response(question_data["question"], technique)
            
            # Оценка ответа
            evaluation = self._evaluate_response(
                question_data, 
                bot_response["response"], 
                bot_response["num_sources"]
            )
            
            # Сохранение результата
            result = {
                "timestamp": datetime.now().isoformat(),
                "test_id": self.test_id,
                "question_id": question_data["id"],
                "question": question_data["question"],
                "category": question_data["category"],
                "expected_type": question_data["expected_type"],
                "technique": technique,
                "response": bot_response["response"],
                "sources": [s["source"] for s in bot_response["sources"]],
                "evaluation": evaluation
            }
            results.append(result)
            
            # Вывод результата
            status = "✅" if evaluation["correct"] else "❌"
            print(f"    {status} {evaluation['completeness']:.1%} полнота | "
                  f"{evaluation['chunks_found']} чанков | "
                  f"{'отказ' if evaluation['is_refusal'] else 'ответ'}")
            
            time.sleep(0.5)  # Небольшая пауза между запросами
        
        total_time = time.time() - start_time
        
        # Статистика по результатам
        stats = self._calculate_statistics(results)
        
        # Сохранение результатов
        self._save_results(results, stats, technique, total_time)
        
        # Вывод итогов
        self._print_summary(stats, total_time)
        
        return {
            "results": results,
            "statistics": stats,
            "test_metadata": {
                "test_id": self.test_id,
                "technique": technique,
                "total_time": total_time,
                "questions_count": len(self.golden_questions)
            }
        }
    
    def _calculate_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Расчет статистики по результатам"""
        
        total = len(results)
        correct_count = sum(1 for r in results if r["evaluation"]["correct"])
        
        # Статистика по типам вопросов
        success_questions = [r for r in results if r["expected_type"] == "success"]
        failure_questions = [r for r in results if r["expected_type"] == "failure"]
        
        success_correct = sum(1 for r in success_questions if r["evaluation"]["correct"])
        failure_correct = sum(1 for r in failure_questions if r["evaluation"]["correct"])
        
        # Средняя полнота ответов
        avg_completeness = sum(r["evaluation"]["completeness"] for r in results) / total
        
        # Статистика по категориям
        categories = {}
        for result in results:
            cat = result["category"]
            if cat not in categories:
                categories[cat] = {"total": 0, "correct": 0}
            categories[cat]["total"] += 1
            if result["evaluation"]["correct"]:
                categories[cat]["correct"] += 1
        
        for cat in categories:
            categories[cat]["accuracy"] = categories[cat]["correct"] / categories[cat]["total"]
        
        return {
            "overall_accuracy": correct_count / total,
            "total_questions": total,
            "correct_answers": correct_count,
            "success_questions": {
                "total": len(success_questions),
                "correct": success_correct,
                "accuracy": success_correct / len(success_questions) if success_questions else 0
            },
            "failure_questions": {
                "total": len(failure_questions), 
                "correct": failure_correct,
                "accuracy": failure_correct / len(failure_questions) if failure_questions else 0
            },
            "average_completeness": avg_completeness,
            "categories": categories
        }
    
    def _save_results(self, results: List[Dict[str, Any]], stats: Dict[str, Any], 
                     technique: str, total_time: float):
        """Сохранение результатов тестирования"""
        
        # Создание папки для результатов
        results_dir = Path("test_results")
        results_dir.mkdir(exist_ok=True)
        
        # Сохранение подробных результатов
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = results_dir / f"golden_set_test_{technique}_{timestamp}.json"
        
        test_data = {
            "metadata": {
                "test_id": self.test_id,
                "timestamp": datetime.now().isoformat(),
                "technique": technique,
                "total_time": total_time,
                "questions_count": len(self.golden_questions)
            },
            "statistics": stats,
            "detailed_results": results
        }
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Результаты сохранены: {results_file}")
    
    def _print_summary(self, stats: Dict[str, Any], total_time: float):
        """Вывод итоговой статистики"""
        
        print("\n" + "="*60)
        print("📊 ИТОГОВАЯ СТАТИСТИКА")
        print("="*60)
        
        print(f"🎯 Общая точность: {stats['overall_accuracy']:.1%} "
              f"({stats['correct_answers']}/{stats['total_questions']})")
        
        print(f"✅ Известные темы: {stats['success_questions']['accuracy']:.1%} "
              f"({stats['success_questions']['correct']}/{stats['success_questions']['total']})")
        
        print(f"❌ Неизвестные темы: {stats['failure_questions']['accuracy']:.1%} "
              f"({stats['failure_questions']['correct']}/{stats['failure_questions']['total']})")
        
        print(f"📈 Средняя полнота: {stats['average_completeness']:.1%}")
        print(f"⏱️  Время тестирования: {total_time:.1f} сек")
        
        print(f"\n📂 Статистика по категориям:")
        for category, cat_stats in stats['categories'].items():
            print(f"  {category}: {cat_stats['accuracy']:.1%} "
                  f"({cat_stats['correct']}/{cat_stats['total']})")


def main():
    """Основная функция для запуска тестирования"""
    
    # Конфигурация RAG-бота
    config = RAGConfig(vector_db_path="chroma_db")
    
    # Создание тестировщика
    tester = GoldenSetTester(config)
    
    # Запуск тестирования для разных техник
    techniques = ["base", "few_shot", "chain_of_thought"]
    
    for technique in techniques:
        print(f"\n{'='*60}")
        print(f"🧪 ТЕСТИРОВАНИЕ ТЕХНИКИ: {technique.upper()}")
        print('='*60)
        
        try:
            results = tester.run_test(technique)
            
            print(f"\n✅ Тестирование {technique} завершено успешно")
            
        except Exception as e:
            print(f"\n❌ Ошибка при тестировании {technique}: {e}")
        
        print("\n" + "-"*60)
        time.sleep(2)  # Пауза между техниками


if __name__ == "__main__":
    main()
