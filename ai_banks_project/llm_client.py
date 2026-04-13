import requests
import json
from typing import Any, Union

LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"

def generate_survey_from_journey(journey: Union[str, dict], hint: str = None) -> dict:

    if isinstance(journey, dict):
        journey_text = json.dumps(journey, ensure_ascii=False)
    else:
        journey_text = str(journey)
    
    user_content = f"Путь клиента: {journey_text}"
    if hint:
        user_content += f"\n\nДополнительная подсказка: {hint}"
    
    from prompts import SYSTEM_PROMPT
    
    payload = {
        "model": "local-model",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ],
        "temperature": 0.3,
        "max_tokens": 1024,
        "stream": False
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(LM_STUDIO_URL, json=payload, headers=headers, timeout=120)
        response.raise_for_status()
        result = response.json()
        
        content = result["choices"][0]["message"]["content"].strip()
        

        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            
        return json.loads(content)
        
    except requests.exceptions.ConnectionError:
        raise ConnectionError("Не удалось подключиться к LM Studio. Убедись, что сервер запущен на localhost:1234")
    except requests.exceptions.Timeout:
        raise TimeoutError("Превышено время ожидания ответа от модели")
    except json.JSONDecodeError as e:
        raise ValueError(f"Модель вернула невалидный JSON: {content[:200]}... Ошибка парсинга: {e}")
    except Exception as e:
        raise RuntimeError(f"Ошибка при генерации: {type(e).__name__}: {e}")