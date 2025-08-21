#!/usr/bin/env python3
"""
Анализатор покрытия базы знаний
Создает детальный отчет о покрытии тем и выявляет пробелы
"""

import json
import sqlite3
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Any
import re
from datetime import datetime

class CoverageAnalyzer:
    """Анализатор покрытия базы знаний"""
    
    def __init__(self, knowledge_base_path="knowledge_base", logs_path="logs/query_logs/queries.db"):
        """
        Инициализация анализатора
        
        Args:
            knowledge_base_path: Путь к базе знаний
            logs_path: Путь к базе данных логов
        """
        self.knowledge_base_path = Path(knowledge_base_path)
        self.logs_path = Path(logs_path)
        
    def analyze_knowledge_base_structure(self) -> Dict[str, Any]:
        """Анализ структуры базы знаний"""
        print("📁 Анализ структуры базы знаний...")
        
        structure = {
            'categories': {},
            'total_files': 0,
            'total_size_bytes': 0,
            'file_sizes': [],
            'category_distribution': {}
        }
        
        # Обход всех файлов
        for file_path in self.knowledge_base_path.rglob("*.txt"):
            if file_path.is_file():
                structure['total_files'] += 1
                
                # Размер файла
                file_size = file_path.stat().st_size
                structure['total_size_bytes'] += file_size
                structure['file_sizes'].append(file_size)
                
                # Категория (папка)
                category = file_path.parent.name
                if category not in structure['categories']:
                    structure['categories'][category] = {
                        'files': [],
                        'count': 0,
                        'total_size': 0
                    }
                
                structure['categories'][category]['files'].append(file_path.name)
                structure['categories'][category]['count'] += 1
                structure['categories'][category]['total_size'] += file_size
        
        # Распределение по категориям
        for category, data in structure['categories'].items():
            structure['category_distribution'][category] = {
                'count': data['count'],
                'percentage': (data['count'] / structure['total_files']) * 100,
                'avg_size': data['total_size'] / data['count'] if data['count'] > 0 else 0
            }
        
        return structure
    
    def analyze_content_topics(self) -> Dict[str, Any]:
        """Анализ тем в контенте"""
        print("🔍 Анализ тем и сущностей...")
        
        topics = {
            'entities': defaultdict(int),
            'keywords': defaultdict(int),
            'removed_entities': [],
            'categories_coverage': {},
            'content_stats': {}
        }
        
        all_text = ""
        category_texts = defaultdict(str)
        
        # Сбор всего текста
        for file_path in self.knowledge_base_path.rglob("*.txt"):
            if file_path.is_file():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        all_text += content + " "
                        
                        category = file_path.parent.name
                        category_texts[category] += content + " "
                        
                        # Поиск удаленных сущностей
                        removed_pattern = r'\[УДАЛЕНО: ([^\]]+)\]'
                        removed_matches = re.findall(removed_pattern, content)
                        topics['removed_entities'].extend(removed_matches)
                        
                except Exception as e:
                    print(f"Ошибка чтения {file_path}: {e}")
        
        # Анализ ключевых слов
        words = re.findall(r'\b[А-ЯA-Z][а-яa-z]+\b', all_text)
        topics['keywords'] = dict(Counter(words).most_common(50))
        
        # Статистика по категориям
        for category, text in category_texts.items():
            word_count = len(text.split())
            char_count = len(text)
            
            topics['categories_coverage'][category] = {
                'word_count': word_count,
                'char_count': char_count,
                'unique_words': len(set(text.lower().split())),
                'removed_entities': len(re.findall(r'\[УДАЛЕНО:', text))
            }
        
        # Общая статистика контента
        topics['content_stats'] = {
            'total_words': len(all_text.split()),
            'total_chars': len(all_text),
            'unique_words': len(set(all_text.lower().split())),
            'removed_entities_count': len(topics['removed_entities']),
            'unique_removed_entities': list(set(topics['removed_entities']))
        }
        
        return topics
    
    def analyze_query_logs(self) -> Dict[str, Any]:
        """Анализ логов запросов"""
        print("📊 Анализ логов запросов...")
        
        if not self.logs_path.exists():
            return {'error': 'Логи не найдены'}
        
        try:
            conn = sqlite3.connect(self.logs_path)
            cursor = conn.cursor()
            
            # Общая статистика
            cursor.execute("SELECT COUNT(*) FROM query_logs")
            total_queries = cursor.fetchone()[0]
            
            if total_queries == 0:
                return {'error': 'Нет записей в логах'}
            
            # Успешные vs неуспешные
            cursor.execute("SELECT response_successful, COUNT(*) FROM query_logs GROUP BY response_successful")
            success_stats = dict(cursor.fetchall())
            
            # Топ неуспешных запросов
            cursor.execute("""
                SELECT query_text, COUNT(*) as freq 
                FROM query_logs 
                WHERE response_successful = 0 
                GROUP BY query_text 
                ORDER BY freq DESC 
                LIMIT 10
            """)
            failed_queries = cursor.fetchall()
            
            # Статистика по количеству найденных чанков
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN chunks_found = 0 THEN '0 чанков'
                        WHEN chunks_found <= 2 THEN '1-2 чанка'
                        WHEN chunks_found <= 5 THEN '3-5 чанков'
                        ELSE '5+ чанков'
                    END as chunk_range,
                    COUNT(*) as count
                FROM query_logs 
                GROUP BY chunk_range
            """)
            chunk_distribution = dict(cursor.fetchall())
            
            # Средние метрики
            cursor.execute("""
                SELECT 
                    AVG(response_time_ms) as avg_time,
                    AVG(chunks_found) as avg_chunks,
                    AVG(response_length) as avg_length
                FROM query_logs
            """)
            avg_metrics = cursor.fetchone()
            
            # Анализ источников
            cursor.execute("SELECT sources FROM query_logs WHERE sources != '[]'")
            sources_data = cursor.fetchall()
            
            all_sources = []
            for row in sources_data:
                try:
                    sources = json.loads(row[0])
                    all_sources.extend(sources)
                except:
                    continue
            
            source_usage = dict(Counter(all_sources).most_common(10))
            
            conn.close()
            
            return {
                'total_queries': total_queries,
                'success_stats': success_stats,
                'success_rate': (success_stats.get(1, 0) / total_queries) * 100,
                'failed_queries': failed_queries,
                'chunk_distribution': chunk_distribution,
                'avg_metrics': {
                    'response_time_ms': round(avg_metrics[0] or 0, 2),
                    'chunks_found': round(avg_metrics[1] or 0, 2),
                    'response_length': round(avg_metrics[2] or 0, 2)
                },
                'source_usage': source_usage
            }
            
        except Exception as e:
            return {'error': f'Ошибка анализа логов: {e}'}
    
    def identify_knowledge_gaps(self, query_analysis: Dict[str, Any], content_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Выявление пробелов в знаниях"""
        print("🚨 Выявление пробелов в знаниях...")
        
        gaps = {
            'content_gaps': [],
            'query_gaps': [],
            'coverage_issues': [],
            'recommendations': []
        }
        
        # Пробелы из удаленного контента
        if content_analysis.get('content_stats', {}).get('unique_removed_entities'):
            gaps['content_gaps'] = content_analysis['content_stats']['unique_removed_entities']
        
        # Пробелы из неуспешных запросов
        if query_analysis.get('failed_queries'):
            gaps['query_gaps'] = [query[0] for query in query_analysis['failed_queries'][:5]]
        
        # Проблемы покрытия
        if query_analysis.get('success_rate', 100) < 80:
            gaps['coverage_issues'].append(f"Низкий процент успеха: {query_analysis['success_rate']:.1f}%")
        
        if content_analysis.get('content_stats', {}).get('removed_entities_count', 0) > 0:
            gaps['coverage_issues'].append(f"Удалено {content_analysis['content_stats']['removed_entities_count']} упоминаний сущностей")
        
        # Рекомендации
        gaps['recommendations'] = self._generate_recommendations(gaps, content_analysis, query_analysis)
        
        return gaps
    
    def _generate_recommendations(self, gaps: Dict, content_analysis: Dict, query_analysis: Dict) -> List[str]:
        """Генерация рекомендаций по улучшению"""
        recommendations = []
        
        # Рекомендации по контенту
        if gaps['content_gaps']:
            recommendations.append(f"Восстановить информацию о сущностях: {', '.join(gaps['content_gaps'][:3])}")
        
        # Рекомендации по категориям
        categories = content_analysis.get('categories_coverage', {})
        if categories:
            min_category = min(categories.items(), key=lambda x: x[1]['word_count'])
            if min_category[1]['word_count'] < 1000:
                recommendations.append(f"Расширить категорию '{min_category[0]}' (только {min_category[1]['word_count']} слов)")
        
        # Рекомендации по запросам
        if query_analysis.get('success_rate', 100) < 90:
            recommendations.append("Улучшить качество ответов - низкий процент успешных запросов")
        
        if gaps['query_gaps']:
            recommendations.append(f"Добавить информацию для частых неуспешных запросов")
        
        # Общие рекомендации
        if not recommendations:
            recommendations.append("База знаний в хорошем состоянии, можно добавить больше деталей")
        
        return recommendations
    
    def generate_coverage_report(self) -> Dict[str, Any]:
        """Генерация полного отчета о покрытии"""
        print("\n📈 ГЕНЕРАЦИЯ ОТЧЕТА О ПОКРЫТИИ БАЗЫ ЗНАНИЙ")
        print("="*60)
        
        # Анализы
        structure = self.analyze_knowledge_base_structure()
        content = self.analyze_content_topics()
        queries = self.analyze_query_logs()
        gaps = self.identify_knowledge_gaps(queries, content)
        
        # Итоговый отчет
        report = {
            'timestamp': datetime.now().isoformat(),
            'structure_analysis': structure,
            'content_analysis': content,
            'query_analysis': queries,
            'knowledge_gaps': gaps,
            'summary': {
                'total_files': structure['total_files'],
                'total_categories': len(structure['categories']),
                'removed_entities': len(content['content_stats']['unique_removed_entities']),
                'total_queries': queries.get('total_queries', 0),
                'success_rate': queries.get('success_rate', 0),
                'main_gaps': gaps['content_gaps'][:3],
                'top_recommendations': gaps['recommendations'][:3]
            }
        }
        
        return report
    
    def print_report(self, report: Dict[str, Any]):
        """Печать отчета в читаемом виде"""
        print("\n📊 ОТЧЕТ О ПОКРЫТИИ БАЗЫ ЗНАНИЙ")
        print("="*60)
        
        # Общая информация
        summary = report['summary']
        print(f"📁 Файлов в базе: {summary['total_files']}")
        print(f"📂 Категорий: {summary['total_categories']}")
        print(f"🗑️  Удаленных сущностей: {summary['removed_entities']}")
        print(f"❓ Всего запросов: {summary['total_queries']}")
        print(f"✅ Процент успеха: {summary['success_rate']:.1f}%")
        print()
        
        # Структура
        print("📁 СТРУКТУРА БАЗЫ ЗНАНИЙ:")
        for category, data in report['structure_analysis']['category_distribution'].items():
            print(f"   {category}: {data['count']} файлов ({data['percentage']:.1f}%)")
        print()
        
        # Удаленные сущности
        if summary['main_gaps']:
            print("🚨 ОСНОВНЫЕ ПРОБЕЛЫ (удаленные сущности):")
            for gap in summary['main_gaps']:
                print(f"   - {gap}")
            print()
        
        # Неуспешные запросы
        if report['query_analysis'].get('failed_queries'):
            print("❌ ЧАСТЫЕ НЕУСПЕШНЫЕ ЗАПРОСЫ:")
            for query, count in report['query_analysis']['failed_queries'][:5]:
                print(f"   - {query} ({count} раз)")
            print()
        
        # Рекомендации
        print("💡 РЕКОМЕНДАЦИИ ПО УЛУЧШЕНИЮ:")
        for i, rec in enumerate(summary['top_recommendations'], 1):
            print(f"   {i}. {rec}")
        print()
        
        # Статистика источников
        if report['query_analysis'].get('source_usage'):
            print("📚 САМЫЕ ИСПОЛЬЗУЕМЫЕ ИСТОЧНИКИ:")
            for source, count in list(report['query_analysis']['source_usage'].items())[:5]:
                print(f"   - {source}: {count} раз")
        
        print("\n✅ Отчет завершен!")
    
    def save_report(self, report: Dict[str, Any], filename: str = "coverage_report.json"):
        """Сохранение отчета в файл"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"💾 Отчет сохранен в {filename}")

def main():
    """Основная функция"""
    analyzer = CoverageAnalyzer()
    
    # Генерация отчета
    report = analyzer.generate_coverage_report()
    
    # Печать отчета
    analyzer.print_report(report)
    
    # Сохранение отчета
    analyzer.save_report(report)

if __name__ == "__main__":
    main()
