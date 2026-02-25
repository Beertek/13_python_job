import requests
import json
from datetime import datetime
import time
from collections import Counter
import re
from typing import List, Dict, Any
import os


class HHParser:
    def __init__(self):
        self.base_url = "https://api.hh.ru/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def search_vacancies(self, text: str, area: str = None, pages: int = 5) -> List[Dict]:
        """
        Поиск вакансий по заданным параметрам
        """
        all_vacancies = []
        
        # Получаем ID региона если указан
        area_id = None
        if area:
            area_id = self._get_area_id(area)
        
        params = {
            'text': text,
            'per_page': 100,  # Максимальное количество на странице
            'page': 0
        }
        
        if area_id:
            params['area'] = area_id
        
        for page in range(pages):
            params['page'] = page
            print(f"Загрузка страницы {page + 1}...")
            
            try:
                response = self.session.get(f"{self.base_url}vacancies", params=params)
                response.raise_for_status()
                
                data = response.json()
                vacancies = data.get('items', [])
                
                if not vacancies:
                    break
                
                # Получаем детальную информацию по каждой вакансии
                for vacancy in vacancies:
                    full_vacancy = self._get_vacancy_details(vacancy['id'])
                    if full_vacancy:
                        all_vacancies.append(full_vacancy)
                    time.sleep(0.2)  # Задержка чтобы не превысить лимиты API
                
                if len(vacancies) < 100:
                    break
                    
            except Exception as e:
                print(f"Ошибка при загрузке страницы {page}: {e}")
                break
        
        return all_vacancies
    
    def _get_area_id(self, area_name: str) -> int:
        """
        Получение ID региона по названию
        """
        try:
            response = self.session.get(f"{self.base_url}areas")
            response.raise_for_status()
            
            areas = response.json()
            return self._find_area_id(areas, area_name)
        except:
            return None
    
    def _find_area_id(self, areas: List, area_name: str) -> int:
        """
        Рекурсивный поиск ID региона
        """
        for area in areas:
            if area['name'].lower() == area_name.lower():
                return area['id']
            if area.get('areas'):
                result = self._find_area_id(area['areas'], area_name)
                if result:
                    return result
        return None
    
    def _get_vacancy_details(self, vacancy_id: str) -> Dict:
        """
        Получение детальной информации о вакансии
        """
        try:
            response = self.session.get(f"{self.base_url}vacancies/{vacancy_id}")
            response.raise_for_status()
            return response.json()
        except:
            return None
    
    def extract_requirements(self, vacancy: Dict) -> List[str]:
        """
        Извлечение требований из описания вакансии
        """
        requirements = []
        
        # Извлекаем из названия
        name = vacancy.get('name', '').lower()
        name_keywords = re.findall(r'[a-zA-Zа-яА-Я0-9#+]+', name)
        requirements.extend(name_keywords)
        
        # Извлекаем из описания
        description = vacancy.get('description', '').lower()
        
        # Извлекаем из ключевых навыков (если есть)
        key_skills = vacancy.get('key_skills', [])
        for skill in key_skills:
            requirements.append(skill.get('name', '').lower())
        
        # Извлекаем из требований в описании
        description_text = description
        
        # Список популярных технологий и навыков для поиска
        tech_keywords = [
            'python', 'java', 'javascript', 'c++', 'c#', 'php', 'ruby', 'go', 'rust',
            'django', 'flask', 'fastapi', 'spring', 'laravel', 'rails',
            'react', 'vue', 'angular', 'jquery', 'node.js',
            'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'oracle',
            'docker', 'kubernetes', 'jenkins', 'git', 'ci/cd',
            'aws', 'azure', 'gcp', 'linux', 'windows',
            'machine learning', 'deep learning', 'ai', 'data science',
            'tensorflow', 'pytorch', 'scikit-learn', 'pandas', 'numpy',
            'html', 'css', 'scss', 'less', 'bootstrap',
            'rest', 'graphql', 'grpc', 'soap',
            'agile', 'scrum', 'kanban', 'jira', 'confluence',
            'teamwork', 'leadership', 'communication', 'english',
            'стрессоустойчивость', 'коммуникабельность', 'ответственность'
        ]
        
        for keyword in tech_keywords:
            if keyword in description_text or keyword in name:
                requirements.append(keyword)
        
        return requirements
    
    def analyze_vacancies(self, vacancies: List[Dict], search_query: str) -> Dict:
        """
        Анализ вакансий и подсчет статистики
        """
        total_vacancies = len(vacancies)
        
        if total_vacancies == 0:
            return {
                'keywords': search_query,
                'count': 0,
                'average_salary': 0,
                'salary_stats': {'min': 0, 'max': 0, 'avg': 0},
                'requirements': [],
                'date': datetime.now().isoformat()
            }
        
        # Сбор всех требований
        all_requirements = []
        salaries = []
        
        for vacancy in vacancies:
            # Сбор зарплат
            salary = vacancy.get('salary')
            if salary and salary.get('from'):
                salaries.append(salary.get('from'))
            
            # Сбор требований
            requirements = self.extract_requirements(vacancy)
            all_requirements.extend(requirements)
        
        # Подсчет частоты требований
        req_counter = Counter(all_requirements)
        total_requirements = len(all_requirements)
        
        # Формирование списка требований с процентами
        requirements_list = []
        for req_name, req_count in req_counter.most_common():
            percent = (req_count / total_requirements) * 100 if total_requirements > 0 else 0
            requirements_list.append({
                'name': req_name,
                'count': req_count,
                'percent': round(percent, 2)
            })
        
        # Статистика по зарплатам
        salary_stats = {}
        if salaries:
            salary_stats = {
                'min': min(salaries),
                'max': max(salaries),
                'avg': round(sum(salaries) / len(salaries), 2)
            }
        
        return {
            'keywords': search_query,
            'count': total_vacancies,
            'average_salary': round(sum(salaries) / len(salaries), 2) if salaries else 0,
            'salary_stats': salary_stats,
            'requirements': requirements_list,
            'date': datetime.now().isoformat()
        }


class VacancyAnalyzer:
    def __init__(self):
        self.parser = HHParser()
        self.results = []
    
    def analyze_multiple_queries(self, queries: List[Dict]) -> List[Dict]:
        """
        Анализ нескольких поисковых запросов
        """
        for query in queries:
            print(f"\nАнализ запроса: {query['text']}")
            print(f"Регион: {query.get('area', 'вся Россия')}")
            
            vacancies = self.parser.search_vacancies(
                text=query['text'],
                area=query.get('area'),
                pages=query.get('pages', 5)
            )
            
            analysis = self.parser.analyze_vacancies(vacancies, query['text'])
            analysis['area'] = query.get('area', 'вся Россия')
            
            self.results.append(analysis)
            
            # Вывод результатов в консоль
            self._print_analysis(analysis)
            
            # Сохраняем промежуточные результаты
            self.save_results()
            
            time.sleep(1)  # Задержка между запросами
        
        return self.results
    
    def _print_analysis(self, analysis: Dict):
        """
        Вывод анализа в консоль
        """
        print(f"\n{'='*50}")
        print(f"Запрос: {analysis['keywords']}")
        print(f"Регион: {analysis.get('area', 'вся Россия')}")
        print(f"Найдено вакансий: {analysis['count']}")
        print(f"Средняя зарплата: {analysis['average_salary']} руб.")
        
        if analysis['salary_stats']:
            stats = analysis['salary_stats']
            print(f"Зарплатный диапазон: {stats.get('min', 0)} - {stats.get('max', 0)} руб.")
        
        print(f"\nТребования:")
        for req in analysis['requirements'][:20]:  # Показываем топ-20
            print(f"  {req['name']}: {req['count']} ({req['percent']}%)")
        
        print(f"{'='*50}\n")
    
    def save_results(self, filename: str = "vacancy_analysis.json"):
        """
        Сохранение результатов в JSON файл
        """
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        print(f"Результаты сохранены в {filename}")
    
    def save_detailed_results(self, filename: str = "vacancy_analysis_detailed.json"):
        """
        Сохранение детальных результатов с дополнительной аналитикой
        """
        detailed_results = []
        
        for result in self.results:
            detailed_result = result.copy()
            
            # Добавляем дополнительную аналитику
            if result['requirements']:
                # Топ-10 требований
                detailed_result['top_10_requirements'] = result['requirements'][:10]
                
                # Группировка по категориям (можно расширить)
                categories = self._categorize_requirements(result['requirements'])
                detailed_result['categories'] = categories
            
            detailed_results.append(detailed_result)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(detailed_results, f, ensure_ascii=False, indent=2)
        print(f"Детальные результаты сохранены в {filename}")
    
    def _categorize_requirements(self, requirements: List[Dict]) -> Dict:
        """
        Категоризация требований
        """
        categories = {
            'programming_languages': [],
            'frameworks': [],
            'databases': [],
            'devops': [],
            'soft_skills': [],
            'other': []
        }
        
        lang_keywords = ['python', 'java', 'javascript', 'c++', 'c#', 'php', 'ruby', 'go']
        framework_keywords = ['django', 'flask', 'spring', 'react', 'vue', 'angular']
        db_keywords = ['sql', 'mysql', 'postgresql', 'mongodb', 'redis']
        devops_keywords = ['docker', 'kubernetes', 'jenkins', 'git', 'ci/cd', 'aws']
        soft_keywords = ['teamwork', 'communication', 'leadership', 'ответственность']
        
        for req in requirements:
            name = req['name'].lower()
            if any(keyword in name for keyword in lang_keywords):
                categories['programming_languages'].append(req)
            elif any(keyword in name for keyword in framework_keywords):
                categories['frameworks'].append(req)
            elif any(keyword in name for keyword in db_keywords):
                categories['databases'].append(req)
            elif any(keyword in name for keyword in devops_keywords):
                categories['devops'].append(req)
            elif any(keyword in name for keyword in soft_keywords):
                categories['soft_skills'].append(req)
            else:
                categories['other'].append(req)
        
        return categories


def main():
    """
    Основная функция для запуска анализа
    """
    analyzer = VacancyAnalyzer()
    
    # Пример запросов для анализа
    queries = [
        {
            'text': 'python developer',
            'area': 'Москва',
            'pages': 3  # Количество страниц для парсинга
        },
        {
            'text': 'frontend developer',
            'area': 'Москва',
            'pages': 3
        },
        {
            'text': 'data scientist',
            'area': 'Москва',
            'pages': 3
        },
        {
            'text': 'жестянщик',
            'area': 'Москва',
            'pages': 2
        }
    ]
    
    # Запуск анализа
    results = analyzer.analyze_multiple_queries(queries)
    
    # Сохранение результатов
    analyzer.save_results()
    analyzer.save_detailed_results()
    
    print("\nАнализ завершен!")
    print(f"Проанализировано запросов: {len(results)}")


if __name__ == "__main__":
    main()