#!/usr/bin/env python3
"""
Анализатор логов RAG-системы
Выявляет проблемы, паттерны неудач и рекомендации по улучшению
"""

import pandas as pd
import json
import re
from collections import defaultdict, Counter
from datetime import datetime
from pathlib import Path
# import matplotlib.pyplot as plt  # Убрано для совместимости
# import seaborn as sns

class LogAnalyzer:
    """Анализатор логов RAG-системы"""
    
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self.df = None
        self.load_logs()
    
    def load_logs(self):
        """Загрузка логов из CSV"""
        try:
            # Читаем CSV, пропуская первую строку если это заголовки
            self.df = pd.read_csv(self.csv_path)
            
            # Если первая строка не заголовки, добавляем их
            if 'timestamp' not in self.df.columns:
                self.df.columns = [
                    'timestamp', 'query_text', 'chunks_found', 'chunks_used',
                    'response_length', 'response_successful', 'sources',
                    'similarity_scores', 'response_time_ms', 'error_message',
                    'session_id', 'user_feedback'
                ]
            
            # Парсинг данных
            self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
            self.df['response_successful'] = self.df['response_successful'].astype(bool)
            
            print(f"📊 Загружено {len(self.df)} записей логов")
            
        except Exception as e:
            print(f"❌ Ошибка загрузки логов: {e}")
            self.df = pd.DataFrame()
    
    def analyze_failures(self):
        """Анализ неудачных запросов"""
        print("\n🔍 АНАЛИЗ НЕУДАЧНЫХ ЗАПРОСОВ")
        print("="*50)
        
        if self.df.empty:
            print("Нет данных для анализа")
            return
        
        # Общая статистика
        total_queries = len(self.df)
        failed_queries = len(self.df[~self.df['response_successful']])
        success_rate = (total_queries - failed_queries) / total_queries * 100
        
        print(f"📈 Общая статистика:")
        print(f"  Всего запросов: {total_queries}")
        print(f"  Неудачных: {failed_queries}")
        print(f"  Успешность: {success_rate:.1f}%")
        
        # Анализ неудачных запросов
        failed_df = self.df[~self.df['response_successful']]
        
        if not failed_df.empty:
            print(f"\n❌ Темы с частыми неудачами:")
            failure_queries = failed_df['query_text'].value_counts()
            for query, count in failure_queries.head(10).items():
                print(f"  '{query}' - {count} раз")
            
            # Анализ паттернов неудач
            print(f"\n🔍 Паттерны неудачных запросов:")
            patterns = self._analyze_query_patterns(failed_df['query_text'].tolist())
            for pattern, count in patterns.most_common(5):
                print(f"  {pattern}: {count} запросов")
        
        return {
            'total_queries': total_queries,
            'failed_queries': failed_queries,
            'success_rate': success_rate,
            'failure_patterns': failure_queries.to_dict() if not failed_df.empty else {}
        }
    
    def analyze_sources(self):
        """Анализ источников и релевантности"""
        print("\n📚 АНАЛИЗ ИСТОЧНИКОВ")
        print("="*50)
        
        if self.df.empty:
            return
        
        # Парсинг источников
        all_sources = []
        for sources_str in self.df['sources']:
            if pd.notna(sources_str) and sources_str != '[]':
                try:
                    sources = json.loads(sources_str.replace("'", '"'))
                    all_sources.extend(sources)
                except:
                    pass
        
        # Статистика по источникам
        source_counter = Counter(all_sources)
        
        print(f"📊 Наиболее используемые источники:")
        for source, count in source_counter.most_common(10):
            print(f"  {source}: {count} раз")
        
        # Анализ качества источников
        print(f"\n🎯 Анализ качества источников:")
        self._analyze_source_quality()
        
        return source_counter
    
    def analyze_knowledge_gaps(self):
        """Анализ пробелов в знаниях"""
        print("\n🕳️  АНАЛИЗ ПРОБЕЛОВ В ЗНАНИЯХ")
        print("="*50)
        
        # Читаем список удаленных сущностей
        removed_entities_file = Path("db_prepare/removed_entities.txt")
        removed_entities = []
        if removed_entities_file.exists():
            with open(removed_entities_file, 'r', encoding='utf-8') as f:
                removed_entities = [line.strip() for line in f if line.strip()]
        
        # Анализ запросов на удаленные сущности
        removed_queries = []
        for _, row in self.df.iterrows():
            query = row['query_text'].lower()
            for entity in removed_entities:
                if entity.lower() in query:
                    removed_queries.append({
                        'query': row['query_text'],
                        'entity': entity,
                        'successful': row['response_successful'],
                        'chunks_found': row['chunks_found']
                    })
        
        print(f"🎯 Запросы по удаленным сущностям:")
        for rq in removed_queries:
            status = "✅ Корректно отклонен" if not rq['successful'] else "❌ Неверно обработан"
            print(f"  '{rq['query']}' ({rq['entity']}) - {status}")
        
        # Выявление других пробелов
        print(f"\n🔍 Другие потенциальные пробелы:")
        failed_df = self.df[~self.df['response_successful']]
        unique_failures = failed_df['query_text'].unique()
        
        for query in unique_failures[:5]:
            if not any(entity.lower() in query.lower() for entity in removed_entities):
                print(f"  '{query}' - возможный новый пробел")
        
        return {
            'removed_entities_queries': removed_queries,
            'potential_gaps': unique_failures.tolist()
        }
    
    def _analyze_query_patterns(self, queries):
        """Анализ паттернов в запросах"""
        patterns = Counter()
        
        for query in queries:
            query_lower = query.lower()
            
            # Определение типа вопроса
            if query_lower.startswith(('кто такой', 'кто такая')):
                patterns['Вопросы о персонажах'] += 1
            elif query_lower.startswith(('что такое', 'что это')):
                patterns['Вопросы о предметах/понятиях'] += 1
            elif 'расскажи' in query_lower:
                patterns['Запросы на рассказ'] += 1
            elif any(word in query_lower for word in ['как', 'каким образом']):
                patterns['Вопросы о процессах'] += 1
            else:
                patterns['Другие типы вопросов'] += 1
        
        return patterns
    
    def _analyze_source_quality(self):
        """Анализ качества источников"""
        
        # Группировка по успешности и источникам
        successful_queries = self.df[self.df['response_successful']]
        failed_queries = self.df[~self.df['response_successful']]
        
        # Анализ распределения по категориям
        categories = defaultdict(lambda: {'success': 0, 'failed': 0})
        
        for _, row in self.df.iterrows():
            if pd.notna(row['sources']) and row['sources'] != '[]':
                try:
                    sources = json.loads(row['sources'].replace("'", '"'))
                    for source in sources:
                        category = source.split('/')[0] if '/' in source else 'unknown'
                        if row['response_successful']:
                            categories[category]['success'] += 1
                        else:
                            categories[category]['failed'] += 1
                except:
                    pass
        
        print("📂 Качество по категориям:")
        for category, stats in categories.items():
            total = stats['success'] + stats['failed']
            if total > 0:
                success_rate = stats['success'] / total * 100
                print(f"  {category}: {success_rate:.1f}% успешности ({stats['success']}/{total})")
    
    def generate_recommendations(self):
        """Генерация рекомендаций по улучшению"""
        print("\n💡 РЕКОМЕНДАЦИИ ПО УЛУЧШЕНИЮ")
        print("="*50)
        
        # Анализ данных
        failure_analysis = self.analyze_failures()
        source_analysis = self.analyze_sources()
        gap_analysis = self.analyze_knowledge_gaps()
        
        recommendations = []
        
        # Рекомендации по успешности
        if failure_analysis['success_rate'] < 80:
            recommendations.append({
                'priority': 'ВЫСОКИЙ',
                'area': 'Промпты',
                'issue': f"Низкая общая успешность ({failure_analysis['success_rate']:.1f}%)",
                'action': 'Улучшить промпты и логику обработки запросов'
            })
        
        # Рекомендации по пробелам знаний
        removed_queries = gap_analysis['removed_entities_queries']
        incorrect_removed = [rq for rq in removed_queries if rq['successful']]
        
        if incorrect_removed:
            recommendations.append({
                'priority': 'ВЫСОКИЙ',
                'area': 'База знаний',
                'issue': f"Неправильная обработка удаленных сущностей ({len(incorrect_removed)} случаев)",
                'action': 'Добавить информацию об удаленных сущностях или улучшить логику отказов'
            })
        
        # Рекомендации по частым неудачам
        if failure_analysis['failure_patterns']:
            top_failure = max(failure_analysis['failure_patterns'].items(), key=lambda x: x[1])
            if top_failure[1] > 2:
                recommendations.append({
                    'priority': 'СРЕДНИЙ',
                    'area': 'Контент',
                    'issue': f"Частые неудачи по теме '{top_failure[0]}' ({top_failure[1]} раз)",
                    'action': 'Расширить или улучшить информацию по данной теме'
                })
        
        # Вывод рекомендаций
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. [{rec['priority']}] {rec['area']}")
            print(f"   Проблема: {rec['issue']}")
            print(f"   Действие: {rec['action']}")
            print()
        
        return recommendations
    
    def create_summary_report(self):
        """Создание итогового отчета"""
        print("\n📋 ИТОГОВЫЙ ОТЧЕТ ПО АНАЛИЗУ ЛОГОВ")
        print("="*60)
        
        # Запуск всех анализов
        failure_analysis = self.analyze_failures()
        source_analysis = self.analyze_sources()
        gap_analysis = self.analyze_knowledge_gaps()
        recommendations = self.generate_recommendations()
        
        # Сохранение отчета
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_queries': failure_analysis['total_queries'],
                'success_rate': failure_analysis['success_rate'],
                'failed_queries': failure_analysis['failed_queries']
            },
            'failure_analysis': failure_analysis,
            'source_analysis': dict(source_analysis.most_common(20)),
            'knowledge_gaps': gap_analysis,
            'recommendations': recommendations
        }
        
        # Сохранение в файл
        report_file = Path("logs/log_analysis_report.json")
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Отчет сохранен: {report_file}")
        
        return report


def main():
    """Основная функция анализа"""
    
    # Путь к логам
    log_path = "logs/query_logs/queries.csv"
    
    if not Path(log_path).exists():
        print(f"❌ Файл логов не найден: {log_path}")
        return
    
    # Создание анализатора
    analyzer = LogAnalyzer(log_path)
    
    # Запуск полного анализа
    analyzer.create_summary_report()


if __name__ == "__main__":
    main()
