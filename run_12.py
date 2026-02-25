#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Скрипт для запуска парсера вакансий с hh.ru
"""

import sys
import json
from hh_parser import VacancyAnalyzer


def load_queries_from_file(filename):
    """
    Загрузка запросов из JSON файла
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Файл {filename} не найден")
        return None
    except json.JSONDecodeError:
        print(f"Ошибка в формате JSON файла {filename}")
        return None


def main():
    """
    Основная функция
    """
    print("=" * 60)
    print("Парсер вакансий с hh.ru")
    print("=" * 60)
    
    analyzer = VacancyAnalyzer()
    
    # Проверяем наличие файла с запросами
    queries_file = "queries.json"
    
    if len(sys.argv) > 1:
        queries_file = sys.argv[1]
    
    queries = load_queries_from_file(queries_file)
    
    if not queries:
        # Используем запросы по умолчанию
        queries = [
            {
                'text': 'python developer',
                'area': 'Москва',
                'pages': 3
            },
            {
                'text': 'java developer',
                'area': 'Москва',
                'pages': 3
            },
            {
                'text': 'frontend developer',
                'area': 'Санкт-Петербург',
                'pages': 3
            },
            {
                'text': 'data scientist',
                'area': 'Москва',
                'pages': 2
            }
        ]
        print("Используются запросы по умолчанию")
    
    print(f"Запросов для анализа: {len(queries)}")
    
    # Запуск анализа
    results = analyzer.analyze_multiple_queries(queries)
    
    # Сохранение результатов
    analyzer.save_results("vacancy_analysis.json")
    analyzer.save_detailed_results("vacancy_analysis_detailed.json")
    
    print("\n" + "=" * 60)
    print("Анализ завершен успешно!")
    print("Результаты сохранены в файлы:")
    print("  - vacancy_analysis.json")
    print("  - vacancy_analysis_detailed.json")
    print("=" * 60)


if __name__ == "__main__":
    main()