from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY', '')

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Resume Tailor</title>
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f0f2f5;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
        }
        .card {
            background: white;
            border-radius: 24px;
            padding: 24px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
        h1 {
            font-size: 1.8rem;
            margin: 0 0 8px 0;
            color: #1e293b;
        }
        .sub {
            color: #475569;
            margin-bottom: 24px;
            border-left: 3px solid #3b82f6;
            padding-left: 12px;
        }
        label {
            font-weight: 600;
            display: block;
            margin: 16px 0 6px 0;
            color: #0f172a;
        }
        textarea {
            width: 100%;
            padding: 12px;
            border: 1px solid #cbd5e1;
            border-radius: 16px;
            font-size: 14px;
            background: #f8fafc;
            font-family: inherit;
            min-height: 140px;
        }
        button {
            background: #3b82f6;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 40px;
            font-weight: 600;
            font-size: 16px;
            margin-top: 20px;
            width: 100%;
            cursor: pointer;
        }
        button:hover { background: #2563eb; }
        button:disabled { background: #94a3b8; }
        .result-area {
            background: #f1f5f9;
            border-radius: 20px;
            padding: 16px;
            margin-top: 16px;
            white-space: pre-wrap;
            font-size: 14px;
            line-height: 1.5;
            max-height: 400px;
            overflow-y: auto;
        }
        .flex-buttons {
            display: flex;
            gap: 12px;
            margin-top: 12px;
        }
        .secondary {
            background: #475569;
        }
        .status {
            margin-top: 12px;
            padding: 10px;
            border-radius: 12px;
            font-size: 13px;
            display: none;
        }
        .status.error { background: #fee2e2; color: #991b1b; }
        .status.success { background: #dcfce7; color: #15803d; }
        hr { margin: 20px 0; }
    </style>
</head>
<body>
<div class="container">
    <div class="card">
        <h1>AI Resume Tailor</h1>
        <div class="sub">Адаптируй резюме под любую вакансию</div>

        <label>Твоё резюме</label>
        <textarea id="resume" placeholder="Вставь текст твоего резюме..."></textarea>

        <label>Текст вакансии</label>
        <textarea id="jobDesc" placeholder="Скопируй описание вакансии..."></textarea>

        <button id="adaptBtn">Адаптировать резюме</button>

        <div id="status" class="status"></div>

        <div id="resultBlock" style="display: none;">
            <hr>
            <h3>Результат</h3>
            <div id="resultText" class="result-area"></div>
            <div class="flex-buttons">
                <button id="copyBtn" class="secondary">Скопировать</button>
                <button id="compareBtn" class="secondary">Было / Стало</button>
            </div>
        </div>
    </div>
</div>

<script>
    const resumeTextarea = document.getElementById('resume');
    const jobTextarea = document.getElementById('jobDesc');
    const adaptBtn = document.getElementById('adaptBtn');
    const resultBlock = document.getElementById('resultBlock');
    const resultTextDiv = document.getElementById('resultText');
    const copyBtn = document.getElementById('copyBtn');
    const compareBtn = document.getElementById('compareBtn');
    const statusDiv = document.getElementById('status');

    let currentResult = '';

    function showStatus(message, isError) {
        statusDiv.textContent = message;
        statusDiv.className = isError ? 'status error' : 'status success';
        statusDiv.style.display = 'block';
        setTimeout(function() {
            statusDiv.style.display = 'none';
        }, 4000);
    }

    adaptBtn.onclick = async function() {
        const resume = resumeTextarea.value.trim();
        const job = jobTextarea.value.trim();

        if (!resume) {
            showStatus('Введите резюме', true);
            return;
        }
        if (!job) {
            showStatus('Введите описание вакансии', true);
            return;
        }

        adaptBtn.disabled = true;
        adaptBtn.innerText = 'Адаптируем...';
        showStatus('Отправляем запрос к ИИ...', false);

        try {
            const response = await fetch('/api/adapt', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ resume: resume, job: job })
            });
            const data = await response.json();
            if (data.error) throw new Error(data.error);
            currentResult = data.result;
            resultTextDiv.innerText = currentResult;
            resultBlock.style.display = 'block';
            showStatus('Готово!', false);
        } catch (err) {
            showStatus('Ошибка: ' + err.message, true);
        } finally {
            adaptBtn.disabled = false;
            adaptBtn.innerText = 'Адаптировать резюме';
        }
    };

    copyBtn.onclick = function() {
        navigator.clipboard.writeText(currentResult);
        showStatus('Скопировано!', false);
    };

    compareBtn.onclick = function() {
        const original = resumeTextarea.value.trim();
        resultTextDiv.innerText = 'БЫЛО:\n' + original + '\n\n---\n\nСТАЛО:\n' + currentResult;
    };
</script>
</body>
</html>
'''

@app.route('/')
def index():
    return HTML

@app.route('/api/adapt', methods=['POST'])
def adapt():
    data = request.json
    resume = data.get('resume', '')
    job = data.get('job', '')
    
    if not resume or not job:
        return jsonify({'error': 'Заполните оба поля'}), 400
    
    prompt = f"""Ты эксперт по резюме. Перепиши резюме под вакансию.
Правила:
1. Не выдумывай опыт и навыки.
2. Используй ключевые слова из вакансии.
3. Убери лишнее.
4. Ответь только новым резюме, без пояснений.

Резюме:
{resume}

Вакансия:
{job}

Адаптированное резюме:"""
    
    try:
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {OPENROUTER_API_KEY}',
                'Content-Type': 'application/json',
            },
            json={
                'model': 'deepseek/deepseek-chat',
                'messages': [{'role': 'user', 'content': prompt}],
                'temperature': 0.5,
                'max_tokens': 2000
            },
            timeout=60
        )
        
        if response.status_code != 200:
            return jsonify({'error': f'API ошибка: {response.status_code}'}), 500
        
        result = response.json()['choices'][0]['message']['content']
        return jsonify({'result': result})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)