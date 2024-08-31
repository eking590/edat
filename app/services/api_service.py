import requests
import re
import json
from typing import Dict, List, Optional
from fastapi import HTTPException

API_KEY = "dPFNmccRAPS77upmo1mQYcYUFXm3a15z"
ENDPOINT_URL = "https://api.mistral.ai/v1/chat/completions"
MODEL = "mistral-tiny"


def format_math_expression(text: str) -> str:
    text = re.sub(r'(\d+)/(\d+)', r'\\frac{\1}{\2}', text)
    text = re.sub(r'(\d+)\^(\d+)', r'\1^{\2}', text)
    symbol_map = {
        '×': '\\times',
        '÷': '\\div',
        '±': '\\pm',
        '≠': '\\neq',
        '≤': '\\leq',
        '≥': '\\geq',
        '∞': '\\infty',
        'π': '\\pi',
        '√': '\\sqrt'
    }
    for symbol, latex in symbol_map.items():
        text = text.replace(symbol, latex)
    return text


def api_request(messages: List[Dict[str, str]], max_tokens: int = 2000) -> str:
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.7
    }
    try:
        response = requests.post(ENDPOINT_URL, json=data, headers=headers)
        response.raise_for_status()
        raw_response = response.text
        print(f'Raw API response: {raw_response}')
        try:
            json_response = response.json()
            return format_math_expression(json_response['choices'][0]['message']['content'])
        except json.JSONDecodeError as e: 
            raise HTTPException(status_code=500, detail=f"Failed to parse JSON response: {str(e)} - Raw Response: {raw_response}")

    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"API request failed: {e}")