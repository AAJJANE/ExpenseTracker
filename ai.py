import re
import requests
import json

from config import MODEL, API_URL


def ai_review(incomes, expenses):
    prompt = f"""Write a short review(up to 3 sentences for a user,
                                whose incomes equal float({incomes})
                                and expenses equal float({expenses}).
                                Your response must be addressed to the user.
                                Do not use any currencies in your response!"""

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "Content-Type": "application/json",
    }

    response = requests.post(API_URL, json=payload)
    json_response = json.loads(response.text)
    cleaned_response = re.sub(r'<think>.*?</think>', '', json_response['response'], flags=re.DOTALL)
    return cleaned_response.strip()