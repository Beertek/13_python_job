// Основной JavaScript файл

// Состояние приложения
const appState = {
    currentSearch: null,
    loading: false,
    results: []
};

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    // Подсветка активной страницы в навигации
    highlightActivePage();
    
    // Инициализация форм
    initializeForms();
    
    // Загрузка результатов если есть ID в URL
    loadResultsFromUrl();
});

// Подсветка активной страницы
function highlightActivePage() {
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';
    const navLinks = document.querySelectorAll('.nav-links a');
    
    navLinks.forEach(link => {
        const linkPage = link.getAttribute('href');
        if (linkPage === currentPage) {
            link.classList.add('active');
        }
    });
}

// Инициализация форм
function initializeForms() {
    const searchForm = document.getElementById('searchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', handleSearch);
    }
    
    // Инициализация масок для телефона (если есть)
    const phoneInputs = document.querySelectorAll('input[type="tel"]');
    phoneInputs.forEach(input => {
        input.addEventListener('input', formatPhone);
    });
}

// Обработка поиска
async function handleSearch(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    
    // Показываем загрузку
    showLoader();
    
    // Собираем данные формы
    const searchData = {
        profession: formData.get('profession') || 'парикмахер',
        city: formData.get('city') || 'Москва',
        experience: formData.get('experience') || '',
        salary_from: formData.get('salary_from') || '',
        pages: formData.get('pages') || 2
    };
    
    try {
        // Отправляем запрос на сервер
        const response = await fetch('/api/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(searchData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Сохраняем результаты в localStorage для восстановления
            localStorage.setItem('lastSearch', JSON.stringify(searchData));
            
            // Перенаправляем на страницу с результатами
            window.location.href = `/result?id=${data.result_id}`;
        } else {
            showError(data.error || 'Произошла ошибка при поиске');
        }
    } catch (error) {
        console.error('Search error:', error);
        showError('Ошибка соединения с сервером');
    } finally {
        hideLoader();
    }
}

// Загрузка результатов из URL
async function loadResultsFromUrl() {
    const urlParams = new URLSearchParams(window.location.search);
    const resultId = urlParams.get('id');
    
    if (resultId && window.location.pathname.includes('result.html')) {
        showLoader();
        
        try {
            // Загружаем статистику
            const statsResponse = await fetch(`/api/stats/${resultId}`);
            const stats = await statsResponse.json();
            
            if (!stats.error) {
                displayStats(stats);
            }
        } catch (error) {
            console.error('Error loading stats:', error);
        } finally {
            hideLoader();
        }
    }
}

// Отображение статистики
function displayStats(stats) {
    const statsContainer = document.getElementById('statsContainer');
    if (!statsContainer) return;
    
    const statsHtml = `
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">${stats.count || 0}</div>
                <div class="stat-label">Всего вакансий</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${formatSalary(stats.average_salary || 0)} ₽</div>
                <div class="stat-label">Средняя зарплата</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${Object.keys(stats.specializations || {}).length}</div>
                <div class="stat-label">Специализаций</div>
            </div>
        </div>
        
        <div class="card">
            <h3 class="card-title">Востребованные навыки</h3>
            <ul class="requirements-list">
                ${(stats.requirements || []).map(req => `
                    <li>
                        <span class="req-name">${req.name}</span>
                        <span class="req-count">${req.count}</span>
                        <span class="req-percent">${req.percent}%</span>
                    </li>
                `).join('')}
            </ul>
        </div>
    `;
    
    statsContainer.innerHTML = statsHtml;
}

// Фильтрация таблицы
function filterTable() {
    const input = document.getElementById('tableSearch');
    const filter = input.value.toLowerCase();
    const table = document.getElementById('resultsTable');
    const rows = table.getElementsByTagName('tr');
    
    for (let i = 1; i < rows.length; i++) {
        const row = rows[i];
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(filter) ? '' : 'none';
    }
}

// Сортировка таблицы
function sortTable(columnIndex) {
    const table = document.getElementById('resultsTable');
    const rows = Array.from(table.rows).slice(1);
    const isNumeric = columnIndex === 4 || columnIndex === 5; // Индексы числовых колонок
    
    rows.sort((a, b) => {
        const aVal = a.cells[columnIndex].textContent;
        const bVal = b.cells[columnIndex].textContent;
        
        if (isNumeric) {
            const aNum = parseFloat(aVal) || 0;
            const bNum = parseFloat(bVal) || 0;
            return aNum - bNum;
        }
        
        return aVal.localeCompare(bVal, 'ru');
    });
    
    // Обновляем порядок строк
    const tbody = table.getElementsByTagName('tbody')[0];
    rows.forEach(row => tbody.appendChild(row));
}

// Экспорт в CSV
function exportToCSV() {
    const table = document.getElementById('resultsTable');
    const rows = [];
    
    // Заголовки
    const headers = [];
    for (let cell of table.rows[0].cells) {
        headers.push(cell.textContent);
    }
    rows.push(headers.join(','));
    
    // Данные
    for (let i = 1; i < table.rows.length; i++) {
        const row = [];
        for (let cell of table.rows[i].cells) {
            row.push(`"${cell.textContent.replace(/"/g, '""')}"`);
        }
        rows.push(row.join(','));
    }
    
    // Скачиваем файл
    const csv = rows.join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'beauty_specialists.csv';
    link.click();
}

// Вспомогательные функции
function showLoader() {
    const loader = document.getElementById('loader');
    if (loader) loader.classList.add('active');
    appState.loading = true;
}

function hideLoader() {
    const loader = document.getElementById('loader');
    if (loader) loader.classList.remove('active');
    appState.loading = false;
}

function showError(message) {
    const alert = document.createElement('div');
    alert.className = 'alert alert-danger fade-in';
    alert.textContent = message;
    
    const container = document.querySelector('.container');
    container.insertBefore(alert, container.firstChild);
    
    setTimeout(() => alert.remove(), 5000);
}

function showSuccess(message) {
    const alert = document.createElement('div');
    alert.className = 'alert alert-success fade-in';
    alert.textContent = message;
    
    const container = document.querySelector('.container');
    container.insertBefore(alert, container.firstChild);
    
    setTimeout(() => alert.remove(), 3000);
}

function formatSalary(salary) {
    if (!salary) return '0';
    return salary.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
}

function formatPhone(event) {
    let input = event.target;
    let value = input.value.replace(/\D/g, '');
    
    if (value.length > 0) {
        if (value.length <= 1) {
            value = '+7 (' + value;
        } else if (value.length <= 4) {
            value = '+7 (' + value.slice(1, 4);
        } else if (value.length <= 7) {
            value = '+7 (' + value.slice(1, 4) + ') ' + value.slice(4, 7);
        } else if (value.length <= 9) {
            value = '+7 (' + value.slice(1, 4) + ') ' + value.slice(4, 7) + '-' + value.slice(7, 9);
        } else {
            value = '+7 (' + value.slice(1, 4) + ') ' + value.slice(4, 7) + '-' + value.slice(7, 9) + '-' + value.slice(9, 11);
        }
    }
    
    input.value = value;
}

// Сохранение настроек поиска
function saveSearchSettings() {
    const settings = {
        profession: document.getElementById('profession')?.value,
        city: document.getElementById('city')?.value,
        pages: document.getElementById('pages')?.value
    };
    
    localStorage.setItem('searchSettings', JSON.stringify(settings));
    showSuccess('Настройки сохранены');
}

// Загрузка сохраненных настроек
function loadSearchSettings() {
    const settings = localStorage.getItem('searchSettings');
    if (settings) {
        const parsed = JSON.parse(settings);
        
        Object.keys(parsed).forEach(key => {
            const input = document.getElementById(key);
            if (input && parsed[key]) {
                input.value = parsed[key];
            }
        });
        
        showSuccess('Настройки загружены');
    }
}

// Очистка формы
function clearForm() {
    const form = document.getElementById('searchForm');
    if (form) {
        form.reset();
        showSuccess('Форма очищена');
    }
}