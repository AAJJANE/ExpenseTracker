import aiohttp
import re
from config import MODEL, API_URL


async def ai_review_async(incomes, expenses):
    prompt = f"""Write a short review(up to 3 sentences for a user,
                                whose incomes equal float({incomes})
                                and expenses equal float({expenses}).
                                Your response must be addressed to the user.
                                Do not use any currencies in your response! Again, NO CURRENCIES IN YOUR RESPONSE!!! but if you have them, then make it Russian ruble"""

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "Content-Type": "application/json",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(API_URL, json=payload) as response:
            json_response = await response.json()
            cleaned_response = re.sub(r'<think>.*?</think>',
                                      '', json_response['response'],
                                      flags=re.DOTALL)
            return cleaned_response.strip()
