import requests
import json
from typing import Dict, List, Optional
from fastapi import HTTPException

API_KEY = "dPFNmccRAPS77upmo1mQYcYUFXm3a15z"
ENDPOINT_URL = "https://api.mistral.ai/v1/chat/completions"
MODEL = "mistral-tiny"

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
        return response.json()['choices'][0]['message']['content']
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"API request failed: {e}")

# Add more utility functions if needed...
