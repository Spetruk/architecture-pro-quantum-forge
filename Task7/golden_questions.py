#!/usr/bin/env python3
"""
"Золотой набор" тестовых вопросов для оценки качества RAG-системы
Автоматические тесты покрытия базы знаний с эталонными ответами
"""

import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class GoldenQuestion:
    """Эталонный тестовый вопрос"""
    question: str
    category: str
    expected_entities: List[str]  # Ожидаемые сущности в ответе
    expected_sources: List[str]   # Ожидаемые файлы-источники
    difficulty: str               # easy, medium, hard
    should_succeed: bool          # Ожидается ли успешный ответ
    keywords: List[str]           # Ключевые слова для проверки
    description: str              # Описание теста

class GoldenQuestionSet:
    """Набор эталонных вопросов для тестирования"""
    
    def __init__(self):
        """Инициализация с предопределенными вопросами"""
        self.questions = self._create_golden_questions()
    
    def _create_golden_questions(self) -> List[GoldenQuestion]:
        """Создание эталонного набора вопросов"""
        
        questions = [
            # === ПЕРСОНАЖИ (characters) ===
            GoldenQuestion(
                question="Кто такой Arin Solara и чем он занимается?",
                category="characters",
                expected_entities=["Arin Solara"],
                expected_sources=["characters/Arin Solara.txt"],
                difficulty="easy",
                should_succeed=True,
                keywords=["Arin", "Solara", "исследователь", "пилот"],
                description="Базовый вопрос о главном персонаже"
            ),
            
            GoldenQuestion(
                question="Расскажи о роботе KX-13",
                category="characters", 
                expected_entities=["KX-13"],
                expected_sources=["characters/KX-13.txt"],
                difficulty="easy",
                should_succeed=True,
                keywords=["KX-13", "робот", "дроид"],
                description="Вопрос о роботе-персонаже"
            ),
            
            GoldenQuestion(
                question="Какие отношения между Arin Solara и Lyra Oris?",
                category="characters",
                expected_entities=["Arin Solara", "Lyra Oris"],
                expected_sources=["characters/Arin Solara.txt", "characters/Lyra Oris.txt"],
                difficulty="medium",
                should_succeed=True,
                keywords=["Arin", "Lyra", "отношения"],
                description="Вопрос о связях между персонажами"
            ),
            
            # === УДАЛЕННЫЕ ПЕРСОНАЖИ (пробелы) ===
            GoldenQuestion(
                question="Что ты знаешь о персонаже Xarn Velgor?",
                category="characters",
                expected_entities=["Xarn Velgor"],
                expected_sources=[],
                difficulty="easy",
                should_succeed=False,
                keywords=["Xarn", "Velgor"],
                description="ПРОБЕЛ: Удаленный персонаж"
            ),
            
            # === ТЕХНОЛОГИИ (technologies) ===
            GoldenQuestion(
                question="Что такое Lumen Blade и как он работает?",
                category="technologies",
                expected_entities=["Lumen Blade"],
                expected_sources=["technologies/Lumen Blade.txt"],
                difficulty="easy",
                should_succeed=True,
                keywords=["Lumen", "Blade", "меч", "световой"],
                description="Базовый вопрос о технологии"
            ),
            
            GoldenQuestion(
                question="Объясни принцип работы Rift Engine",
                category="technologies",
                expected_entities=["Rift Engine"],
                expected_sources=["technologies/Rift Engine.txt"],
                difficulty="medium",
                should_succeed=True,
                keywords=["Rift", "Engine", "двигатель"],
                description="Технический вопрос о двигателе"
            ),
            
            # === УДАЛЕННЫЕ ТЕХНОЛОГИИ (пробелы) ===
            GoldenQuestion(
                question="Как работает технология Synth Flux?",
                category="technologies", 
                expected_entities=["Synth Flux"],
                expected_sources=[],
                difficulty="easy",
                should_succeed=False,
                keywords=["Synth", "Flux"],
                description="ПРОБЕЛ: Удаленная технология"
            ),
            
            # === ЛОКАЦИИ (locations) ===
            GoldenQuestion(
                question="Опиши планету Elyndar",
                category="locations",
                expected_entities=["Elyndar"],
                expected_sources=["locations/Elyndar.txt"],
                difficulty="easy",
                should_succeed=True,
                keywords=["Elyndar", "планета"],
                description="Базовый вопрос о локации"
            ),
            
            GoldenQuestion(
                question="Какой климат на планете Aurelia Prime?",
                category="locations",
                expected_entities=["Aurelia Prime"],
                expected_sources=["locations/Aurelia Prime.txt"],
                difficulty="medium",
                should_succeed=True,
                keywords=["Aurelia", "Prime", "климат"],
                description="Детальный вопрос о планете"
            ),
            
            # === УДАЛЕННЫЕ ЛОКАЦИИ (пробелы) ===
            GoldenQuestion(
                question="Где находится Void Core и что это такое?",
                category="locations",
                expected_entities=["Void Core"],
                expected_sources=[],
                difficulty="easy",
                should_succeed=False,
                keywords=["Void", "Core"],
                description="ПРОБЕЛ: Удаленная локация"
            ),
            
            # === СОБЫТИЯ (events) ===
            GoldenQuestion(
                question="Что произошло во время Echo Wars?",
                category="events",
                expected_entities=["Echo Wars"],
                expected_sources=["events/Echo Wars.txt"],
                difficulty="easy",
                should_succeed=True,
                keywords=["Echo", "Wars", "война"],
                description="Базовый вопрос о событии"
            ),
            
            GoldenQuestion(
                question="Какие последствия имел Edict 99?",
                category="events",
                expected_entities=["Edict 99"],
                expected_sources=["events/Edict 99.txt"],
                difficulty="medium",
                should_succeed=True,
                keywords=["Edict", "99", "указ"],
                description="Вопрос о последствиях события"
            ),
            
            # === СЛОЖНЫЕ ВОПРОСЫ (cross-category) ===
            GoldenQuestion(
                question="Какую роль играл Arin Solara в Echo Wars?",
                category="mixed",
                expected_entities=["Arin Solara", "Echo Wars"],
                expected_sources=["characters/Arin Solara.txt", "events/Echo Wars.txt"],
                difficulty="hard",
                should_succeed=True,
                keywords=["Arin", "Echo", "Wars", "роль"],
                description="Сложный вопрос связывающий персонажа и событие"
            ),
            
            GoldenQuestion(
                question="Какие технологии использовались на планете Krael?",
                category="mixed",
                expected_entities=["Krael"],
                expected_sources=["locations/Krael.txt"],
                difficulty="hard",
                should_succeed=True,
                keywords=["Krael", "технологии"],
                description="Сложный вопрос о технологиях локации"
            ),
            
            # === ОБЩИЕ ВОПРОСЫ ===
            GoldenQuestion(
                question="Перечисли всех главных персонажей",
                category="general",
                expected_entities=["Arin Solara", "Lyra Oris", "Kade Rhaul"],
                expected_sources=["characters/"],
                difficulty="medium",
                should_succeed=True,
                keywords=["персонажи", "главные"],
                description="Общий вопрос о персонажах"
            ),
            
            GoldenQuestion(
                question="Какие планеты упоминаются в историях?",
                category="general",
                expected_entities=["Elyndar", "Aurelia Prime", "Krael"],
                expected_sources=["locations/"],
                difficulty="medium", 
                should_succeed=True,
                keywords=["планеты", "миры"],
                description="Общий вопрос о локациях"
            ),
        ]
        
        return questions
    
    def get_questions_by_category(self, category: str) -> List[GoldenQuestion]:
        """Получить вопросы по категории"""
        return [q for q in self.questions if q.category == category]
    
    def get_questions_by_difficulty(self, difficulty: str) -> List[GoldenQuestion]:
        """Получить вопросы по сложности"""
        return [q for q in self.questions if q.difficulty == difficulty]
    
    def get_gap_questions(self) -> List[GoldenQuestion]:
        """Получить вопросы, выявляющие пробелы (should_succeed=False)"""
        return [q for q in self.questions if not q.should_succeed]
    
    def get_coverage_questions(self) -> List[GoldenQuestion]:
        """Получить вопросы для проверки покрытия (should_succeed=True)"""
        return [q for q in self.questions if q.should_succeed]

class GoldenTestRunner:
    """Исполнитель эталонных тестов"""
    
    def __init__(self, search_function=None):
        """
        Инициализация тестера
        
        Args:
            search_function: Функция поиска для тестирования (query -> result)
        """
        self.golden_set = GoldenQuestionSet()
        self.search_function = search_function
    
    def evaluate_answer(self, question: GoldenQuestion, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Оценка ответа на эталонный вопрос
        
        Args:
            question: Эталонный вопрос
            result: Результат поиска/ответа
            
        Returns:
            Оценка качества ответа
        """
        evaluation = {
            'question': question.question,
            'category': question.category,
            'difficulty': question.difficulty,
            'expected_success': question.should_succeed,
            'actual_success': result.get('success', False),
            'chunks_found': result.get('chunks_found', 0),
            'sources_found': result.get('sources', []),
            'response': result.get('response', ''),
            'scores': {},
            'pass': False
        }
        
        # Проверка успешности
        success_match = evaluation['expected_success'] == evaluation['actual_success']
        evaluation['scores']['success_match'] = 1.0 if success_match else 0.0
        
        # Проверка наличия ожидаемых сущностей в ответе
        entity_score = 0.0
        if question.expected_entities and evaluation['response']:
            found_entities = 0
            for entity in question.expected_entities:
                if entity.lower() in evaluation['response'].lower():
                    found_entities += 1
            entity_score = found_entities / len(question.expected_entities)
        evaluation['scores']['entity_coverage'] = entity_score
        
        # Проверка источников
        source_score = 0.0
        if question.expected_sources and evaluation['sources_found']:
            expected_files = [src for src in question.expected_sources if src.endswith('.txt')]
            if expected_files:
                found_sources = 0
                for expected in expected_files:
                    if any(expected in actual for actual in evaluation['sources_found']):
                        found_sources += 1
                source_score = found_sources / len(expected_files)
        evaluation['scores']['source_accuracy'] = source_score
        
        # Проверка ключевых слов
        keyword_score = 0.0
        if question.keywords and evaluation['response']:
            found_keywords = 0
            for keyword in question.keywords:
                if keyword.lower() in evaluation['response'].lower():
                    found_keywords += 1
            keyword_score = found_keywords / len(question.keywords)
        evaluation['scores']['keyword_presence'] = keyword_score
        
        # Общий балл
        if question.should_succeed:
            # Для успешных вопросов важны все метрики
            overall_score = (
                evaluation['scores']['success_match'] * 0.4 +
                evaluation['scores']['entity_coverage'] * 0.3 +
                evaluation['scores']['source_accuracy'] * 0.2 +
                evaluation['scores']['keyword_presence'] * 0.1
            )
        else:
            # Для пробелов важно только правильное определение неуспеха
            overall_score = evaluation['scores']['success_match']
        
        evaluation['scores']['overall'] = overall_score
        evaluation['pass'] = overall_score >= 0.7  # Порог прохождения теста
        
        return evaluation
    
    def run_golden_tests(self, search_function=None, categories: List[str] = None) -> Dict[str, Any]:
        """
        Запуск эталонных тестов
        
        Args:
            search_function: Функция поиска (опционально)
            categories: Категории для тестирования (опционально)
            
        Returns:
            Результаты тестирования
        """
        if search_function:
            self.search_function = search_function
        
        if not self.search_function:
            raise ValueError("Необходимо предоставить функцию поиска для тестирования")
        
        # Фильтрация вопросов
        questions_to_test = self.golden_set.questions
        if categories:
            questions_to_test = [q for q in questions_to_test if q.category in categories]
        
        print(f"🧪 Запуск эталонных тестов ({len(questions_to_test)} вопросов)...")
        print("="*60)
        
        results = {
            'total_tests': len(questions_to_test),
            'passed_tests': 0,
            'failed_tests': 0,
            'by_category': {},
            'by_difficulty': {},
            'gap_detection': {'correct': 0, 'total': 0},
            'coverage_tests': {'correct': 0, 'total': 0},
            'evaluations': [],
            'summary': {}
        }
        
        # Выполнение тестов
        for i, question in enumerate(questions_to_test, 1):
            print(f"🔍 Тест {i}/{len(questions_to_test)}: {question.question[:60]}...")
            
            # Выполнение поиска
            search_result = self.search_function(question.question)
            
            # Оценка результата
            evaluation = self.evaluate_answer(question, search_result)
            results['evaluations'].append(evaluation)
            
            # Обновление статистики
            if evaluation['pass']:
                results['passed_tests'] += 1
                status = "✅ PASS"
            else:
                results['failed_tests'] += 1
                status = "❌ FAIL"
            
            print(f"   {status} (общий балл: {evaluation['scores']['overall']:.2f})")
            
            # Статистика по категориям
            category = question.category
            if category not in results['by_category']:
                results['by_category'][category] = {'passed': 0, 'total': 0}
            results['by_category'][category]['total'] += 1
            if evaluation['pass']:
                results['by_category'][category]['passed'] += 1
            
            # Статистика по сложности
            difficulty = question.difficulty
            if difficulty not in results['by_difficulty']:
                results['by_difficulty'][difficulty] = {'passed': 0, 'total': 0}
            results['by_difficulty'][difficulty]['total'] += 1
            if evaluation['pass']:
                results['by_difficulty'][difficulty]['passed'] += 1
            
            # Статистика детекции пробелов
            if not question.should_succeed:
                results['gap_detection']['total'] += 1
                if evaluation['expected_success'] == evaluation['actual_success']:
                    results['gap_detection']['correct'] += 1
            else:
                results['coverage_tests']['total'] += 1
                if evaluation['expected_success'] == evaluation['actual_success']:
                    results['coverage_tests']['correct'] += 1
        
        # Итоговая статистика
        pass_rate = (results['passed_tests'] / results['total_tests']) * 100
        gap_detection_rate = (results['gap_detection']['correct'] / results['gap_detection']['total']) * 100 if results['gap_detection']['total'] > 0 else 0
        coverage_rate = (results['coverage_tests']['correct'] / results['coverage_tests']['total']) * 100 if results['coverage_tests']['total'] > 0 else 0
        
        results['summary'] = {
            'pass_rate': pass_rate,
            'gap_detection_accuracy': gap_detection_rate,
            'coverage_accuracy': coverage_rate,
            'total_score': (pass_rate + gap_detection_rate + coverage_rate) / 3
        }
        
        return results
    
    def print_results(self, results: Dict[str, Any]):
        """Печать результатов тестирования"""
        print("\n📊 РЕЗУЛЬТАТЫ ЭТАЛОННОГО ТЕСТИРОВАНИЯ")
        print("="*60)
        
        summary = results['summary']
        print(f"📈 Общий результат: {summary['total_score']:.1f}%")
        print(f"✅ Прошло тестов: {results['passed_tests']}/{results['total_tests']} ({summary['pass_rate']:.1f}%)")
        print(f"🚨 Точность детекции пробелов: {summary['gap_detection_accuracy']:.1f}%")
        print(f"📚 Точность покрытия: {summary['coverage_accuracy']:.1f}%")
        print()
        
        # По категориям
        print("📂 РЕЗУЛЬТАТЫ ПО КАТЕГОРИЯМ:")
        for category, stats in results['by_category'].items():
            rate = (stats['passed'] / stats['total']) * 100
            print(f"   {category}: {stats['passed']}/{stats['total']} ({rate:.1f}%)")
        print()
        
        # По сложности
        print("🎯 РЕЗУЛЬТАТЫ ПО СЛОЖНОСТИ:")
        for difficulty, stats in results['by_difficulty'].items():
            rate = (stats['passed'] / stats['total']) * 100
            print(f"   {difficulty}: {stats['passed']}/{stats['total']} ({rate:.1f}%)")
        print()
        
        # Неуспешные тесты
        failed_evaluations = [e for e in results['evaluations'] if not e['pass']]
        if failed_evaluations:
            print("❌ НЕУСПЕШНЫЕ ТЕСТЫ:")
            for eval in failed_evaluations[:5]:  # Показываем только первые 5
                print(f"   - {eval['question'][:50]}... (балл: {eval['scores']['overall']:.2f})")
        
        print("\n✅ Эталонное тестирование завершено!")

def main():
    """Демонстрация работы с эталонными вопросами"""
    golden_set = GoldenQuestionSet()
    
    print("📋 ЭТАЛОННЫЙ НАБОР ВОПРОСОВ")
    print("="*50)
    print(f"Всего вопросов: {len(golden_set.questions)}")
    
    # Статистика по категориям
    categories = {}
    for q in golden_set.questions:
        categories[q.category] = categories.get(q.category, 0) + 1
    
    print("\n📊 По категориям:")
    for cat, count in categories.items():
        print(f"   {cat}: {count}")
    
    # Пробелы vs покрытие
    gaps = len(golden_set.get_gap_questions())
    coverage = len(golden_set.get_coverage_questions())
    
    print(f"\n🚨 Тестов пробелов: {gaps}")
    print(f"✅ Тестов покрытия: {coverage}")
    
    print("\n💡 Для запуска тестов используйте GoldenTestRunner с функцией поиска")

if __name__ == "__main__":
    main()
