import requests
import json
import time
import re
from collections import Counter
from datetime import datetime
from typing import List, Dict, Optional
import random


class BeautyHHParser:
    def __init__(self):
        self.base_url = "https://api.hh.ru/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Расширенный словарь для бьюти-индустрии
        self.beauty_keywords = {
            'professions': [
                'парикмахер', 'парикмахер-универсал', 'барбер', 'стилист', 'колорист',
                'master', 'топ-стилист', 'bride-стилист', 'свадебный стилист',
                'мужской мастер', 'женский мастер', 'детский мастер'
            ],
            'services': [
                'стрижка', 'стрижки', 'окрашивание', 'укладка', 'прически',
                'мелирование', 'тонирование', 'колорирование', 'омбре', 'шатуш',
                'балаяж', 'airtouch', 'косички', 'плетение', 'химическая завивка',
                'биозавивка', 'ламинирование', 'ботокс', 'кератин',
                'наращивание', 'бритье', 'коррекция бороды', 'моделирование бороды',
                'детские стрижки', 'мужские стрижки', 'женские стрижки'
            ],
            'experience_levels': {
                'без опыта': ['без опыта', 'без опыта работы', 'новичок', 'стажер', 'ученик'],
                'от 1 года': ['опыт от 1 года', 'опыт работы от 1 года', 'стаж от 1 года'],
                'от 1-3 лет': ['опыт от 1 года до 3 лет', 'опыт 1-3 года'],
                'от 3 лет': ['опыт от 3 лет', 'опыт работы от 3 лет', 'стаж от 3 лет']
            }
        }
    
    def search_vacancies(self, text: str, area: str = None, pages: int = 3) -> List[Dict]:
        """Поиск вакансий"""
        all_vacancies = []
        
        # Получаем ID региона
        area_id = self._get_area_id(area) if area else None
        
        # Пробуем разные варианты запросов для более полного поиска
        search_queries = [
            text,
            f"{text} салон",
            f"{text} красота",
            f"{text} барбершоп"
        ]
        
        for query in search_queries:
            params = {
                'text': query,
                'per_page': 50,
                'page': 0,
                'order_by': 'relevance',
                'professional_role': 33  # Код для бьюти-индустрии в hh.ru
            }
            
            if area_id:
                params['area'] = area_id
            
            for page in range(pages):
                params['page'] = page
                
                try:
                    response = self.session.get(f"{self.base_url}vacancies", params=params, timeout=10)
                    response.raise_for_status()
                    
                    data = response.json()
                    vacancies = data.get('items', [])
                    
                    if not vacancies:
                        break
                    
                    for vacancy in vacancies:
                        if vacancy['id'] not in [v['id'] for v in all_vacancies]:
                            full_vacancy = self._get_vacancy_details(vacancy['id'])
                            if full_vacancy:
                                all_vacancies.append(full_vacancy)
                    
                    time.sleep(0.3)  # Задержка для соблюдения лимитов API
                    
                except Exception as e:
                    print(f"Ошибка при загрузке: {e}")
                    continue
            
            time.sleep(1)  # Задержка между разными запросами
        
        return all_vacancies
    
    def _get_area_id(self, area_name: str) -> Optional[int]:
        """Получение ID региона"""
        try:
            response = self.session.get(f"{self.base_url}areas")
            areas = response.json()
            return self._find_area_id(areas, area_name)
        except:
            return None
    
    def _find_area_id(self, areas: List, area_name: str) -> Optional[int]:
        """Рекурсивный поиск ID региона"""
        for area in areas:
            if area_name.lower() in area['name'].lower():
                return area['id']
            if area.get('areas'):
                result = self._find_area_id(area['areas'], area_name)
                if result:
                    return result
        return None
    
    def _get_vacancy_details(self, vacancy_id: str) -> Optional[Dict]:
        """Получение детальной информации о вакансии"""
        try:
            response = self.session.get(f"{self.base_url}vacancies/{vacancy_id}", timeout=10)
            return response.json()
        except:
            return None
    
    def extract_specialist_info(self, vacancy: Dict) -> Optional[Dict]:
        """Извлечение информации о специалисте из вакансии"""
        try:
            name = vacancy.get('name', '')
            description = vacancy.get('description', '')
            salary = vacancy.get('salary', {})
            
            # Определяем специальность
            specialty = self._determine_specialty(name + ' ' + description)
            
            # Определяем опыт работы
            experience = self._determine_experience(description)
            
            # Извлекаем телефон (если есть в контактах)
            phone = self._extract_phone(vacancy)
            
            # Извлекаем email (если есть)
            email = self._extract_email(description)
            
            # Извлекаем имя контактного лица
            contact_name = self._extract_contact_name(vacancy)
            
            # Формируем результат
            specialist = {
                'id': vacancy.get('id'),
                'name': contact_name or 'Не указано',
                'phone': phone or 'Не указан',
                'email': email or 'Не указан',
                'specialty': specialty,
                'experience': experience,
                'salary_from': salary.get('from') if salary else None,
                'salary_to': salary.get('to') if salary else None,
                'currency': salary.get('currency', 'RUR') if salary else None,
                'company': vacancy.get('employer', {}).get('name', 'Не указано'),
                'address': self._extract_address(vacancy),
                'schedule': vacancy.get('schedule', {}).get('name', 'Не указано'),
                'url': vacancy.get('alternate_url'),
                'published_at': vacancy.get('published_at', '')[:10]
            }
            
            return specialist
            
        except Exception as e:
            print(f"Ошибка при извлечении информации: {e}")
            return None
    
    def _determine_specialty(self, text: str) -> str:
        """Определение специальности по тексту"""
        text_lower = text.lower()
        
        if 'барбер' in text_lower or 'barber' in text_lower:
            return 'Барбер'
        elif 'парикмахер-универсал' in text_lower or 'универсал' in text_lower:
            return 'Парикмахер-универсал'
        elif 'колорист' in text_lower:
            return 'Колорист'
        elif 'стилист' in text_lower:
            return 'Стилист'
        elif 'парикмахер' in text_lower:
            return 'Парикмахер'
        else:
            return 'Парикмахер'
    
    def _determine_experience(self, text: str) -> str:
        """Определение требуемого опыта работы"""
        text_lower = text.lower()
        
        for level, keywords in self.beauty_keywords['experience_levels'].items():
            for keyword in keywords:
                if keyword in text_lower:
                    return level
        
        return 'Не указано'
    
    def _extract_phone(self, vacancy: Dict) -> Optional[str]:
        """Извлечение телефона из контактов"""
        try:
            contacts = vacancy.get('contacts', {})
            if contacts:
                phones = contacts.get('phones', [])
                if phones:
                    phone = phones[0].get('formatted', '')
                    if phone:
                        return phone
            
            # Ищем телефон в описании
            description = vacancy.get('description', '')
            phone_pattern = r'(\+7|8)[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}'
            phones = re.findall(phone_pattern, description)
            if phones:
                return phones[0]
                
        except:
            pass
        return None
    
    def _extract_email(self, text: str) -> Optional[str]:
        """Извлечение email из текста"""
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, text)
        return emails[0] if emails else None
    
    def _extract_contact_name(self, vacancy: Dict) -> Optional[str]:
        """Извлечение имени контактного лица"""
        try:
            contacts = vacancy.get('contacts', {})
            if contacts:
                return contacts.get('name')
        except:
            pass
        return None
    
    def _extract_address(self, vacancy: Dict) -> str:
        """Извлечение адреса"""
        try:
            address = vacancy.get('address', {})
            if address:
                city = address.get('city', '')
                street = address.get('street', '')
                building = address.get('building', '')
                
                parts = [p for p in [city, street, building] if p]
                if parts:
                    return ', '.join(parts)
        except:
            pass
        return 'Не указано'
    
    def analyze_vacancies(self, vacancies: List[Dict], search_query: str, area: str) -> Dict:
        """Анализ вакансий"""
        if not vacancies:
            return {
                'count': 0,
                'average_salary': 0,
                'requirements': []
            }
        
        salaries = []
        requirements = []
        
        for vacancy in vacancies:
            # Сбор зарплат
            salary = vacancy.get('salary', {})
            if salary and salary.get('from'):
                salaries.append(salary['from'])
            
            # Сбор требований из описания
            description = vacancy.get('description', '').lower()
            for service in self.beauty_keywords['services']:
                if service in description:
                    requirements.append(service)
        
        # Подсчет статистики
        req_counter = Counter(requirements)
        req_list = [
            {'name': k.capitalize(), 'count': v, 'percent': round(v/len(vacancies)*100, 1)}
            for k, v in req_counter.most_common(15)
        ]
        
        # Статистика по специализациям
        specializations = {}
        for vacancy in vacancies:
            specialty = self._determine_specialty(vacancy.get('name', ''))
            specializations[specialty] = specializations.get(specialty, 0) + 1
        
        # Статистика по опыту
        experience_stats = {}
        for vacancy in vacancies:
            exp = self._determine_experience(vacancy.get('description', ''))
            experience_stats[exp] = experience_stats.get(exp, 0) + 1
        
        return {
            'count': len(vacancies),
            'average_salary': round(sum(salaries)/len(salaries)) if salaries else 0,
            'salary_range': {
                'min': min(salaries) if salaries else 0,
                'max': max(salaries) if salaries else 0
            },
            'requirements': req_list,
            'specializations': specializations,
            'experience_stats': experience_stats
        }