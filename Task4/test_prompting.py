"""
Тестирование различных техник промптинга
Сравнение качества ответов между базовым, few-shot и chain-of-thought подходами
"""

import json
import time
from typing import List, Dict, Any
from app.rag_bot import RAGBot, RAGConfig
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

class PromptingTester:
    """Класс для тестирования техник промптинга"""
    
    def __init__(self):
        self.config = RAGConfig(vector_db_path="../Task3/chroma_db")
        self.bot = RAGBot(self.config)
        
        # Тестовые вопросы
        self.test_questions = [
            "Кто такой Xarn Velgor?",
            "Что такое Synth Flux?",
            "Как работает Lumen Blade?",
            "Где находится Aurelia Prime?",
            "Что произошло в Echo Wars?",
            "Кто такие Wardens?",
            "Расскажи о битве на Krael",
            "Какие технологии используют Wardens?",
            "Что такое Void Core?",
            "Кто такой Arin Solara?"
        ]
        
        # Техники для тестирования
        self.techniques = ["base", "few_shot", "chain_of_thought"]
    
    def test_single_question(self, question: str, technique: str) -> Dict[str, Any]:
        """Тестирование одного вопроса с определенной техникой"""
        print(f"🔍 Тестирование: '{question}' с техникой '{technique}'")
        
        start_time = time.time()
        
        try:
            result = self.bot.generate_response(question, technique)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            return {
                "question": question,
                "technique": technique,
                "response": result["response"],
                "response_time": response_time,
                "num_sources": result["num_sources"],
                "sources": result["sources"],
                "success": True
            }
            
        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time
            
            return {
                "question": question,
                "technique": technique,
                "response": f"Ошибка: {str(e)}",
                "response_time": response_time,
                "num_sources": 0,
                "sources": [],
                "success": False,
                "error": str(e)
            }
    
    def test_all_techniques(self, question: str) -> Dict[str, Any]:
        """Тестирование всех техник на одном вопросе"""
        results = {}
        
        for technique in self.techniques:
            result = self.test_single_question(question, technique)
            results[technique] = result
            
            # Небольшая пауза между запросами
            time.sleep(1)
        
        return results
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Запуск комплексного тестирования"""
        print("🚀 Запуск комплексного тестирования техник промптинга")
        print("=" * 60)
        
        all_results = {}
        technique_stats = {tech: {"total_time": 0, "success_count": 0, "avg_sources": 0} for tech in self.techniques}
        
        for i, question in enumerate(self.test_questions, 1):
            print(f"\n📝 Вопрос {i}/{len(self.test_questions)}: {question}")
            print("-" * 50)
            
            question_results = self.test_all_techniques(question)
            all_results[question] = question_results
            
            # Обновление статистики
            for technique, result in question_results.items():
                technique_stats[technique]["total_time"] += result["response_time"]
                if result["success"]:
                    technique_stats[technique]["success_count"] += 1
                technique_stats[technique]["avg_sources"] += result["num_sources"]
            
            # Вывод результатов для текущего вопроса
            self._print_question_results(question_results)
        
        # Вычисление средних значений
        for technique in self.techniques:
            stats = technique_stats[technique]
            stats["avg_time"] = stats["total_time"] / len(self.test_questions)
            stats["avg_sources"] = stats["avg_sources"] / len(self.test_questions)
            stats["success_rate"] = stats["success_count"] / len(self.test_questions)
        
        return {
            "all_results": all_results,
            "technique_stats": technique_stats,
            "summary": self._generate_summary(technique_stats)
        }
    
    def _print_question_results(self, question_results: Dict[str, Any]):
        """Вывод результатов для одного вопроса"""
        for technique, result in question_results.items():
            status = "✅" if result["success"] else "❌"
            print(f"{status} {technique.upper()}:")
            print(f"   Время: {result['response_time']:.2f}с")
            print(f"   Источников: {result['num_sources']}")
            print(f"   Ответ: {result['response'][:100]}...")
            print()
    
    def _generate_summary(self, technique_stats: Dict[str, Any]) -> str:
        """Генерация сводки результатов"""
        summary = "\n📊 СВОДКА РЕЗУЛЬТАТОВ ТЕСТИРОВАНИЯ\n"
        summary += "=" * 50 + "\n"
        
        for technique, stats in technique_stats.items():
            summary += f"\n🔧 {technique.upper()}:\n"
            summary += f"   Успешность: {stats['success_rate']:.1%}\n"
            summary += f"   Среднее время: {stats['avg_time']:.2f}с\n"
            summary += f"   Среднее источников: {stats['avg_sources']:.1f}\n"
        
        return summary
    
    def save_results(self, results: Dict[str, Any], filename: str = "prompting_test_results.json"):
        """Сохранение результатов в JSON файл"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"💾 Результаты сохранены в {filename}")
        except Exception as e:
            print(f"❌ Ошибка сохранения: {e}")
    
    def compare_responses(self, question: str):
        """Сравнение ответов разных техник на одном вопросе"""
        print(f"\n🔍 СРАВНЕНИЕ ОТВЕТОВ НА ВОПРОС: {question}")
        print("=" * 60)
        
        results = self.test_all_techniques(question)
        
        for technique, result in results.items():
            print(f"\n🤖 {technique.upper()}:")
            print("-" * 30)
            print(f"Время: {result['response_time']:.2f}с")
            print(f"Источников: {result['num_sources']}")
            print(f"Ответ:")
            print(result['response'])
            print()


def main():
    """Основная функция"""
    print("🧪 ТЕСТИРОВАНИЕ ТЕХНИК ПРОМПТИНГА")
    print("=" * 50)
    
    tester = PromptingTester()
    
    # Выбор режима тестирования
    print("\nВыберите режим тестирования:")
    print("1. Комплексное тестирование всех вопросов")
    print("2. Сравнение техник на одном вопросе")
    print("3. Интерактивное тестирование")
    
    choice = input("\nВведите номер (1-3): ").strip()
    
    if choice == "1":
        # Комплексное тестирование
        results = tester.run_comprehensive_test()
        print(results["summary"])
        
        # Сохранение результатов
        save_choice = input("\nСохранить результаты в файл? (y/n): ").strip().lower()
        if save_choice == 'y':
            tester.save_results(results)
    
    elif choice == "2":
        # Сравнение на одном вопросе
        question = input("\nВведите вопрос для сравнения: ").strip()
        if question:
            tester.compare_responses(question)
        else:
            print("❌ Вопрос не введен")
    
    elif choice == "3":
        # Интерактивное тестирование
        print("\n🎯 Интерактивное тестирование")
        print("Введите 'quit' для выхода")
        
        while True:
            question = input("\n❓ Ваш вопрос: ").strip()
            
            if question.lower() in ['quit', 'exit', 'выход']:
                break
            
            if question:
                technique = input("Выберите технику (base/few_shot/chain_of_thought): ").strip()
                if technique not in tester.techniques:
                    technique = "base"
                
                result = tester.test_single_question(question, technique)
                print(f"\n🤖 Ответ ({technique}):")
                print(result["response"])
                print(f"⏱️ Время: {result['response_time']:.2f}с")
                print(f"📚 Источников: {result['num_sources']}")
    
    else:
        print("❌ Неверный выбор")


if __name__ == "__main__":
    main()


