import requests
import re
import json
from typing import Dict, List, Optional
from fastapi import HTTPException

#API_KEY = "dPFNmccRAPS77upmo1mQYcYUFXm3a15z"
#API_KEY = "yia1aigVtSWbrssBKINWyDjtnwRNXem0"
#ENDPOINT_URL = "https://api.mistral.ai/v1/chat/completions"
#MODEL = "mistral-tiny"

# DeepSeek API configuration
API_KEY = "sk-35d2963f6d6745acb0365be04b9d3063"
ENDPOINT_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL = "deepseek-chat"

#def normalize_fraction(text: str) -> str:
    # Convert LaTeX-style \frac{a}{b} or frac{a}{b} to a/b
    #text = re.sub(r'\\?frac\s*{(\d+)}\s*{(\d+)}', r'\1/\2', text)
    # Remove extra whitespace
    #text = re.sub(r'\s+', '', text)
    #return text

def clean_math_language(text: str) -> str:
    # Replace e\timespress or e\\timespress with 'express'
    # Fix common LLM/LaTeX symbol mistakes in words
    text = re.sub(r'e\\?times', 'ex', text, flags=re.IGNORECASE)
    text = re.sub(r'\\?times', 'x', text, flags=re.IGNORECASE)
    #text = re.sub(r'e\\?timestrusive', 'extrusive', text, flags=re.IGNORECASE)
    #text = re.sub(r'e\\?timespress', 'express', text, flags=re.IGNORECASE)
    #text = re.sub(r'e\\?timesplain', 'explain', text, flags=re.IGNORECASE)
    #text = re.sub(r'e\\?timesample', 'example', text, flags=re.IGNORECASE)
    #text = re.sub(r'e\\?etimespands', 'expands', text, flags=re.IGNORECASE)
    #text = re.sub(r'e\\?timesercise', 'exercise', text, flags=re.IGNORECASE)
    text = re.sub(r'e\\?matimesimum', 'maximum', text, flags=re.IGNORECASE)
    #text = re.sub(r'e\\?timesplanation', 'explanation', text, flags=re.IGNORECASE) 
    #text = re.sub(r'e\\?etimesperiment', 'experiment', text, flags=re.IGNORECASE)
    #text = re.sub(r'\\?times', 'times', text, flags=re.IGNORECASE)  # If 'times' is used as a word, not symbol
    #text = re.sub(r'\\?dividend', 'dividend', text, flags=re.IGNORECASE)
    text = re.sub(r'\\?divide', 'divide', text, flags=re.IGNORECASE)
    text = re.sub(r'\\?fraction', 'fraction', text, flags=re.IGNORECASE)
    text = re.sub(r'\\?minus', 'minus', text, flags=re.IGNORECASE) 
    text = re.sub(r'\\?plus', 'plus', text, flags=re.IGNORECASE)
    text = re.sub(r'\\?equals', 'equals', text, flags=re.IGNORECASE)
    text = re.sub(r'\\?equal', 'equal', text, flags=re.IGNORECASE)
    text = re.sub(r'\\?solution', 'solution', text, flags=re.IGNORECASE)
    text = re.sub(r'\\?simplify', 'simplify', text, flags=re.IGNORECASE)
    text = re.sub(r'\\?calculate', 'calculate', text, flags=re.IGNORECASE)
    text = re.sub(r'\\?explain', 'explain', text, flags=re.IGNORECASE)
    text = re.sub(r'\\?express', 'express', text, flags=re.IGNORECASE)
    text = re.sub(r'\\?expression', 'expression', text, flags=re.IGNORECASE)
    text = re.sub(r'\\?extrusive', 'extrusive', text, flags=re.IGNORECASE)
    text = re.sub(r'\\?example', 'example', text, flags=re.IGNORECASE)
    text = re.sub(r'\\?exercise', 'exercise', text, flags=re.IGNORECASE)
    text = re.sub(r'\\?explanation', 'explanation', text, flags=re.IGNORECASE)
    text = re.sub(r'\\?fractional', 'fractional', text, flags=re.IGNORECASE)
    text = re.sub(r'\\?divisible', 'divisible', text, flags=re.IGNORECASE)
    text = re.sub(r'\\?divisor', 'divisor', text, flags=re.IGNORECASE)
    text = re.sub(r'\\?numerator', 'numerator', text, flags=re.IGNORECASE)
    text = re.sub(r'\\?denominator', 'denominator', text, flags=re.IGNORECASE)
    text = re.sub(r'\\?subtraction', 'subtraction', text, flags=re.IGNORECASE)
    text = re.sub(r'\\?addition', 'addition', text, flags=re.IGNORECASE)
    text = re.sub(r'\\?multiplication', 'multiplication', text, flags=re.IGNORECASE)
    text = re.sub(r'\\?division', 'division', text, flags=re.IGNORECASE)
    text = re.sub(r'\\?equals', 'equals', text, flags=re.IGNORECASE)
    text = re.sub(r'\\?equal', 'equal', text, flags=re.IGNORECASE)
    text = re.sub(r'\\?\\timesies', 'xies', text, flags=re.IGNORECASE)
    ##text= re.sub(r'\\?etimesert', 'exert', text, flags=re.IGNORECASE)
    #text = re.sub(r'\\?etimesertion', 'exertion', text, flags=re.IGNORECASE)
    #text = re.sub(r'\\?timesertion', 'assertion', text, flags=re.IGNORECASE)
    #text = re.sub(r'\\?timeserted', 'asserted', text, flags=re.IGNORECASE)
    #text = re.sub(r'\\?timeserting', 'asserting', text, flags=re.IGNORECASE)
    #text = re.sub(r'\\?timesertionally', 'assertionally', text, flags=re.IGNORECASE)
    #text = re.sub(r'\\?timesertions', 'assertions', text, flags=re.IGNORECASE)
    #text = re.sub(r'\\?timesert', 'assert', text, flags=re.IGNORECASE)
    # Add more replacements as needed
    return text
def format_math_expression(text: str) -> str:
     # Convert fractions
    
    text = re.sub(r'(\d+)/(\d+)', r'\\frac{\1}{\2}', text)

    # Convert exponents
    text = re.sub(r'(\d+)\^(\d+)', r'\1^{\2}', text)
    symbol_map = {
        'x': '\\times',
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
            ai_content = json_response['choices'][0]['message']['content']
           # Normalize fractions before formatting math expressions
            #normalized_content = normalize_fraction(ai_content)
            formatted = format_math_expression(ai_content)
            cleaned = clean_math_language(formatted)
            return cleaned
            # return format_math_expression(ai_content)
            #return format_math_expression(normalized_content)
        except json.JSONDecodeError as e: 
            raise HTTPException(status_code=500, detail=f"Failed to parse JSON response: {str(e)} - Raw Response: {raw_response}")

    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"API request failed: {e}")
