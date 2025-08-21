#!/usr/bin/env python3
"""
Комплексная аналитика покрытия и качества базы знаний
Интегрирует все инструменты анализа для полной оценки RAG-системы
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, List

# Добавляем путь к модулям приложения
sys.path.append('./app')

from demo_knowledge_gaps import KnowledgeGapAnalyzer
from coverage_analyzer import CoverageAnalyzer  
from golden_questions import GoldenQuestionSet, GoldenTestRunner
from query_logger import QueryLogger

class ComprehensiveAnalyzer:
    """Комплексный анализатор RAG-системы"""
    
    def __init__(self):
        """Инициализация всех компонентов анализа"""
        print("🚀 Инициализация комплексного анализатора...")
        
        # Компоненты анализа
        self.gap_analyzer = KnowledgeGapAnalyzer()
        self.coverage_analyzer = CoverageAnalyzer()
        self.golden_set = GoldenQuestionSet()
        self.golden_runner = GoldenTestRunner()
        
        print("✅ Инициализация завершена")
    
    def run_comprehensive_analysis(self) -> Dict[str, Any]:
        """Запуск полного анализа системы"""
        print("\n🔍 КОМПЛЕКСНАЯ АНАЛИТИКА RAG-СИСТЕМЫ")
        print("="*60)
        
        results = {
            'timestamp': None,
            'gap_analysis': {},
            'coverage_report': {},
            'golden_tests': {},
            'final_assessment': {},
            'recommendations': []
        }
        
        # 1. Анализ пробелов через поиск
        print("\n1️⃣ Анализ пробелов в знаниях...")
        gap_results = self.gap_analyzer.test_knowledge_gaps()
        results['gap_analysis'] = gap_results
        
        # 2. Анализ покрытия базы знаний
        print("\n2️⃣ Анализ покрытия базы знаний...")
        coverage_report = self.coverage_analyzer.generate_coverage_report()
        results['coverage_report'] = coverage_report
        
        # 3. Эталонное тестирование
        print("\n3️⃣ Эталонное тестирование...")
        golden_results = self.golden_runner.run_golden_tests(
            search_function=self.gap_analyzer.search_knowledge
        )
        results['golden_tests'] = golden_results
        
        # 4. Итоговая оценка
        print("\n4️⃣ Итоговая оценка системы...")
        final_assessment = self._generate_final_assessment(results)
        results['final_assessment'] = final_assessment
        
        # 5. Рекомендации
        recommendations = self._generate_comprehensive_recommendations(results)
        results['recommendations'] = recommendations
        
        # Сохранение результатов
        results['timestamp'] = coverage_report['timestamp']
        
        return results
    
    def _generate_final_assessment(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Генерация итоговой оценки системы"""
        
        # Извлечение ключевых метрик
        gap_metrics = results['gap_analysis']
        coverage_metrics = results['coverage_report']['summary']
        golden_metrics = results['golden_tests']['summary']
        
        # Расчет общих оценок
        coverage_score = (gap_metrics['successful'] / gap_metrics['total_queries']) * 100 if gap_metrics['total_queries'] > 0 else 0
        structure_score = min(100, (coverage_metrics['total_files'] / 30) * 100)  # Оценка полноты структуры
        golden_score = golden_metrics['total_score']
        
        # Детекция пробелов
        gaps_detected = len(coverage_metrics['main_gaps'])
        gap_detection_quality = golden_metrics['gap_detection_accuracy']
        
        # Общий балл системы
        overall_score = (coverage_score * 0.4 + structure_score * 0.2 + golden_score * 0.4)
        
        # Определение уровня системы
        if overall_score >= 90:
            system_level = "Отличный"
            level_description = "Система готова к продакшену"
        elif overall_score >= 75:
            system_level = "Хороший"  
            level_description = "Система работоспособна, требует небольших улучшений"
        elif overall_score >= 60:
            system_level = "Удовлетворительный"
            level_description = "Система функциональна, но требует значительных улучшений"
        else:
            system_level = "Неудовлетворительный"
            level_description = "Система требует серьезной доработки"
        
        assessment = {
            'overall_score': round(overall_score, 1),
            'system_level': system_level,
            'level_description': level_description,
            'component_scores': {
                'knowledge_coverage': round(coverage_score, 1),
                'content_structure': round(structure_score, 1),
                'golden_tests': round(golden_score, 1),
                'gap_detection': round(gap_detection_quality, 1)
            },
            'key_metrics': {
                'total_files': coverage_metrics['total_files'],
                'detected_gaps': gaps_detected,
                'query_success_rate': coverage_metrics['success_rate'],
                'golden_pass_rate': golden_metrics['pass_rate']
            },
            'strengths': [],
            'weaknesses': [],
            'critical_issues': []
        }
        
        # Определение сильных сторон
        if coverage_score >= 80:
            assessment['strengths'].append("Высокое покрытие запросов")
        if structure_score >= 80:
            assessment['strengths'].append("Хорошо структурированная база знаний")
        if golden_score >= 80:
            assessment['strengths'].append("Отличные результаты эталонного тестирования")
        if gap_detection_quality >= 80:
            assessment['strengths'].append("Точная детекция пробелов в знаниях")
        
        # Определение слабых сторон
        if coverage_score < 70:
            assessment['weaknesses'].append("Низкое покрытие пользовательских запросов")
        if gaps_detected > 2:
            assessment['weaknesses'].append(f"Обнаружено {gaps_detected} пробелов в знаниях")
        if golden_metrics['pass_rate'] < 75:
            assessment['weaknesses'].append("Низкий процент прохождения эталонных тестов")
        if gap_detection_quality < 70:
            assessment['weaknesses'].append("Неточная детекция пробелов")
        
        # Критические проблемы
        if coverage_score < 50:
            assessment['critical_issues'].append("Критически низкое покрытие запросов")
        if gaps_detected > 5:
            assessment['critical_issues'].append("Слишком много пробелов в базе знаний")
        if golden_score < 50:
            assessment['critical_issues'].append("Неудовлетворительные результаты тестирования")
        
        return assessment
    
    def _generate_comprehensive_recommendations(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Генерация комплексных рекомендаций"""
        
        recommendations = []
        
        gap_metrics = results['gap_analysis']
        coverage_metrics = results['coverage_report']['summary']
        golden_metrics = results['golden_tests']
        assessment = results['final_assessment']
        
        # Приоритетные рекомендации (на основе критических проблем)
        if assessment['critical_issues']:
            for issue in assessment['critical_issues']:
                if "покрытие запросов" in issue:
                    recommendations.append({
                        'priority': 'КРИТИЧЕСКАЯ',
                        'category': 'Покрытие',
                        'issue': issue,
                        'action': 'Расширить базу знаний, добавить недостающую информацию',
                        'expected_impact': 'Значительное улучшение качества ответов'
                    })
                elif "пробелов" in issue:
                    recommendations.append({
                        'priority': 'КРИТИЧЕСКАЯ', 
                        'category': 'Контент',
                        'issue': issue,
                        'action': 'Восстановить удаленную информацию или добавить альтернативы',
                        'expected_impact': 'Устранение слепых зон бота'
                    })
        
        # Рекомендации по конкретным пробелам
        if coverage_metrics['main_gaps']:
            recommendations.append({
                'priority': 'ВЫСОКАЯ',
                'category': 'Контент',
                'issue': f"Отсутствует информация о: {', '.join(coverage_metrics['main_gaps'])}",
                'action': 'Добавить файлы с информацией об этих сущностях',
                'expected_impact': 'Устранение известных пробелов'
            })
        
        # Рекомендации по неуспешным эталонным тестам
        failed_golden = [e for e in golden_metrics['evaluations'] if not e['pass']]
        if failed_golden:
            failed_categories = list(set(e['category'] for e in failed_golden))
            recommendations.append({
                'priority': 'ВЫСОКАЯ',
                'category': 'Качество',
                'issue': f"Неуспешные эталонные тесты в категориях: {', '.join(failed_categories)}",
                'action': 'Улучшить качество информации в этих категориях',
                'expected_impact': 'Повышение точности ответов'
            })
        
        # Рекомендации по структуре
        structure_analysis = results['coverage_report']['structure_analysis']
        min_category = min(
            structure_analysis['category_distribution'].items(),
            key=lambda x: x[1]['count']
        )
        if min_category[1]['count'] < 5:
            recommendations.append({
                'priority': 'СРЕДНЯЯ',
                'category': 'Структура',
                'issue': f"Категория '{min_category[0]}' содержит мало файлов ({min_category[1]['count']})",
                'action': 'Добавить больше контента в эту категорию',
                'expected_impact': 'Улучшение баланса базы знаний'
            })
        
        # Рекомендации по производительности
        query_analysis = results['coverage_report']['query_analysis']
        if query_analysis.get('avg_metrics', {}).get('response_time_ms', 0) > 500:
            recommendations.append({
                'priority': 'СРЕДНЯЯ',
                'category': 'Производительность',
                'issue': f"Высокое время ответа ({query_analysis['avg_metrics']['response_time_ms']} мс)",
                'action': 'Оптимизировать векторный поиск или уменьшить размер чанков',
                'expected_impact': 'Ускорение работы системы'
            })
        
        # Позитивные рекомендации (если система работает хорошо)
        if assessment['overall_score'] >= 80:
            recommendations.append({
                'priority': 'НИЗКАЯ',
                'category': 'Развитие',
                'issue': 'Система работает хорошо',
                'action': 'Добавить мониторинг пользовательских запросов для выявления новых потребностей',
                'expected_impact': 'Проактивное улучшение системы'
            })
        
        return recommendations
    
    def print_comprehensive_report(self, results: Dict[str, Any]):
        """Печать комплексного отчета"""
        print("\n" + "="*80)
        print("📊 КОМПЛЕКСНЫЙ ОТЧЕТ ПО АНАЛИЗУ RAG-СИСТЕМЫ")
        print("="*80)
        
        assessment = results['final_assessment']
        
        # Общая оценка
        print(f"\n🎯 ОБЩАЯ ОЦЕНКА СИСТЕМЫ: {assessment['overall_score']}/100")
        print(f"📈 Уровень: {assessment['system_level']}")
        print(f"💬 {assessment['level_description']}")
        print()
        
        # Компонентные оценки
        print("📊 ОЦЕНКИ ПО КОМПОНЕНТАМ:")
        for component, score in assessment['component_scores'].items():
            emoji = "🟢" if score >= 80 else "🟡" if score >= 60 else "🔴"
            print(f"   {emoji} {component}: {score}/100")
        print()
        
        # Ключевые метрики
        print("📈 КЛЮЧЕВЫЕ МЕТРИКИ:")
        metrics = assessment['key_metrics']
        print(f"   📁 Файлов в базе: {metrics['total_files']}")
        print(f"   🚨 Обнаруженных пробелов: {metrics['detected_gaps']}")
        print(f"   ✅ Успешность запросов: {metrics['query_success_rate']:.1f}%")
        print(f"   🏆 Прохождение эталонных тестов: {metrics['golden_pass_rate']:.1f}%")
        print()
        
        # Сильные стороны
        if assessment['strengths']:
            print("💪 СИЛЬНЫЕ СТОРОНЫ:")
            for strength in assessment['strengths']:
                print(f"   ✅ {strength}")
            print()
        
        # Слабые стороны
        if assessment['weaknesses']:
            print("⚠️  СЛАБЫЕ СТОРОНЫ:")
            for weakness in assessment['weaknesses']:
                print(f"   ⚠️  {weakness}")
            print()
        
        # Критические проблемы
        if assessment['critical_issues']:
            print("🚨 КРИТИЧЕСКИЕ ПРОБЛЕМЫ:")
            for issue in assessment['critical_issues']:
                print(f"   🚨 {issue}")
            print()
        
        # Рекомендации
        print("💡 РЕКОМЕНДАЦИИ ПО УЛУЧШЕНИЮ:")
        recommendations = results['recommendations']
        
        # Группировка по приоритету
        critical_recs = [r for r in recommendations if r['priority'] == 'КРИТИЧЕСКАЯ']
        high_recs = [r for r in recommendations if r['priority'] == 'ВЫСОКАЯ']
        medium_recs = [r for r in recommendations if r['priority'] == 'СРЕДНЯЯ']
        
        if critical_recs:
            print("   🚨 КРИТИЧЕСКИЕ:")
            for rec in critical_recs:
                print(f"      - {rec['action']}")
        
        if high_recs:
            print("   🔴 ВЫСОКИЙ ПРИОРИТЕТ:")
            for rec in high_recs:
                print(f"      - {rec['action']}")
        
        if medium_recs:
            print("   🟡 СРЕДНИЙ ПРИОРИТЕТ:")
            for rec in medium_recs:
                print(f"      - {rec['action']}")
        
        print("\n" + "="*80)
        print("✅ КОМПЛЕКСНЫЙ АНАЛИЗ ЗАВЕРШЕН")
        print("="*80)
    
    def save_comprehensive_report(self, results: Dict[str, Any], filename: str = "comprehensive_analysis.json"):
        """Сохранение комплексного отчета"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Комплексный отчет сохранен в {filename}")

def main():
    """Основная функция"""
    try:
        # Создание анализатора
        analyzer = ComprehensiveAnalyzer()
        
        # Запуск комплексного анализа
        results = analyzer.run_comprehensive_analysis()
        
        # Печать отчета
        analyzer.print_comprehensive_report(results)
        
        # Сохранение отчета
        analyzer.save_comprehensive_report(results)
        
        print(f"\n🎉 Анализ завершен! Система получила оценку {results['final_assessment']['overall_score']}/100")
        
    except Exception as e:
        print(f"❌ Ошибка во время анализа: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
