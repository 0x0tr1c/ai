const API_URL = 'http://localhost:8000/api/generate';


async function loadHistory() {
    const historyList = document.getElementById('historyList');
    
    try {
        const res = await fetch('http://localhost:8000/api/surveys');
        const items = await res.json();
        
        if (!items.length) {
            historyList.innerHTML = '<p style="color:#666">История пуста</p>';
            return;
        }

        historyList.innerHTML = items.map(item => {
            const date = new Date(item.created_at).toLocaleString('ru-RU');
            let questionsCount = 0;
            let category = '—';
            
            try {
                const parsed = JSON.parse(item.generated_result);
                questionsCount = parsed.questions ? parsed.questions.length : 0;
                category = parsed.category || '—';
            } catch(e) {}
            
            return `
            <div style="border-bottom:1px solid #eee; padding: 0.75rem 0;">
                <div style="display:flex; justify-content:space-between; align-items:start;">
                <div>
                    <strong>${category}</strong><br>
                    <small style="color:#666">${date} | Вопросов: ${questionsCount}</small>
                    ${item.hint ? `<br><small style="color:#999">Подсказка: ${item.hint}</small>` : ''}
                </div>
                <button class="secondary" style="padding:0.4rem 0.8rem; font-size:0.9rem;" 
                    onclick="loadSurveyFromHistory(${item.id})">
                    Открыть
                </button>
                </div>
            </div>
            `;
        }).join('');
    } catch (e) {
        console.error('Ошибка загрузки истории:', e);
        historyList.innerHTML = `<p style="color:#d32f2f">Ошибка: ${e.message}</p>`;
    }
}

async function loadSurveyFromHistory(id) {
    try {
        const res = await fetch(`http://localhost:8000/api/surveys/${id}`);
        const item = await res.json();
        
        let data;
        if (item.user_edited_result) {
            try {
                data = JSON.parse(item.user_edited_result);
            } catch (e) {
                data = JSON.parse(item.generated_result);
            }
        } else {
            data = JSON.parse(item.generated_result);
        }
    
        currentSurveyId = id;
        document.getElementById('jsonEditor').value = JSON.stringify(data, null, 2);
        renderResult(data, item.client_journey, item.hint);
        document.getElementById('result').classList.add('active');
        document.getElementById('result').scrollIntoView({behavior: 'smooth'});
    } catch (e) {
        console.error('Ошибка загрузки опроса:', e);
        alert('Не удалось загрузить опрос');
    }
}

async function generateSurvey() {
    const journey = document.getElementById('journey').value.trim();
    const hint = document.getElementById('hint').value.trim();
    const errorEl = document.getElementById('error');
    const loadingEl = document.getElementById('loading');
    const resultEl = document.getElementById('result');

    errorEl.classList.remove('active');
    if (!journey) {
        errorEl.textContent = 'Введите путь клиента';
        errorEl.classList.add('active');
        return;
    }

    loadingEl.classList.add('active');
    resultEl.classList.remove('active');
    document.getElementById('generateBtn').disabled = true;

    try {
        const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ journey, hint })
    });
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || `Ошибка ${response.status}`);
        }

        const data = await response.json();
        renderResult(data, journey, hint);
        resultEl.classList.add('active');
    } catch (e) {
        errorEl.textContent = `${e.message}`;
        errorEl.classList.add('active');
    } finally {
        loadingEl.classList.remove('active');
        document.getElementById('generateBtn').disabled = false;
    }
}

function renderResult(data, journey, hint) {
    if (!data.questions || !Array.isArray(data.questions)) {
    alert('Модель вернула неожиданный формат. Проверьте логи.');
    console.error('Invalid result:', data);
    return;
    }
    document.getElementById('resCategory').textContent = data.category || '—';
    document.getElementById('resRelevance').textContent = 
    data.relevance !== undefined ? (data.relevance * 100).toFixed(0) + '%' : '—';
    
    const tbody = document.querySelector('#questionsTable tbody');
    tbody.innerHTML = '';
    (data.questions || []).forEach((q, i) => {
    const row = tbody.insertRow();
    row.insertCell(0).textContent = i + 1;
    row.insertCell(1).textContent = q;
    });

    document.getElementById('promptPreview').textContent = 
    `SYSTEM: [см. prompts.py]\n\nUSER: Путь: ${journey}\nПодсказка: ${hint || '—'}`;
    document.getElementById('jsonEditor').value = JSON.stringify(data, null, 2);
}

let currentSurveyId = null;

async function applyEdit() {
    try {
        const edited = JSON.parse(document.getElementById('jsonEditor').value);
        if (currentSurveyId) {
            const response = await fetch(`http://localhost:8000/api/surveys/${currentSurveyId}/edit`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ edited_result: edited })
            });
            
            if (response.ok) {
            alert('Правки применены и сохранены в базе');
            } else {
            const err = await response.json().catch(() => ({}));
            alert(`Правки применены локально, но не сохранены: ${err.detail || 'ошибка сервера'}`);
            }
        } else {
            alert('Правки применены (локально)');
        }
        renderResult(edited, '', '');
    } catch {
        alert('Некорректный JSON');
    }
}

function exportJSON() {
    try {
        const data = JSON.parse(document.getElementById('jsonEditor').value);
        const blob = new Blob([JSON.stringify(data, null, 2)], {type: 'application/json'});
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `survey_${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);
    } catch {
        alert('Не удалось экспортировать: проверьте JSON');
    }
}