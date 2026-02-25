from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import json
import os
from datetime import datetime
from hh_parser_beauty import BeautyHHParser
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
CORS(app)

# Инициализация парсера
parser = BeautyHHParser()

# Хранилище результатов (в реальном проекте лучше использовать БД)
search_results = {}

@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')

@app.route('/data')
def data():
    """Страница с формой поиска"""
    return render_template('data.html')

@app.route('/info')
def info():
    """Страница контактов"""
    return render_template('info.html')

@app.route('/result')
def result():
    """Страница с результатами"""
    result_id = request.args.get('id')
    if result_id and result_id in search_results:
        data = search_results[result_id]
        return render_template('result.html', 
                             results=data['results'],
                             query=data['query'],
                             stats=data['stats'])
    return render_template('result.html', results=None)

@app.route('/api/search', methods=['POST'])
def search():
    """API для поиска вакансий"""
    try:
        data = request.json
        profession = data.get('profession', 'парикмахер')
        city = data.get('city', 'Москва')
        experience = data.get('experience', '')
        salary_from = data.get('salary_from', '')
        pages = int(data.get('pages', 2))
        
        # Формируем поисковый запрос
        search_query = profession
        if 'универсал' in profession.lower():
            search_query = 'парикмахер-универсал'
        elif 'барбер' in profession.lower():
            search_query = 'барбер'
        
        # Выполняем поиск
        vacancies = parser.search_vacancies(
            text=search_query,
            area=city,
            pages=pages
        )
        
        # Анализируем результаты
        analysis = parser.analyze_vacancies(vacancies, search_query, city)
        
        # Преобразуем в формат для таблицы
        results = []
        for vacancy in vacancies[:50]:  # Ограничиваем до 50 результатов
            specialist = parser.extract_specialist_info(vacancy)
            if specialist:
                results.append(specialist)
        
        # Генерируем ID для результатов
        result_id = datetime.now().strftime('%Y%m%d%H%M%S')
        
        # Сохраняем результаты
        search_results[result_id] = {
            'results': results,
            'query': {
                'profession': profession,
                'city': city,
                'experience': experience,
                'salary_from': salary_from
            },
            'stats': {
                'total': analysis['count'],
                'avg_salary': analysis['average_salary'],
                'requirements': analysis['requirements'][:10],
                'hairdresser_stats': analysis.get('hairdresser_stats', {})
            }
        }
        
        return jsonify({
            'success': True,
            'result_id': result_id,
            'count': len(results),
            'stats': analysis
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stats/<result_id>')
def get_stats(result_id):
    """Получение статистики по результатам поиска"""
    if result_id in search_results:
        return jsonify(search_results[result_id]['stats'])
    return jsonify({'error': 'Results not found'}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)