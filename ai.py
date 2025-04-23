import re
import multiprocessing
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import UserMessage
from azure.core.credentials import AzureKeyCredential
from config import DEEPSEEK_API_KEY


def _make_request(incomes, expenses, result_queue):
    try:
        endpoint = "https://models.github.ai/inference"
        model_name = "deepseek/DeepSeek-R1"
        token = DEEPSEEK_API_KEY

        client = ChatCompletionsClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(token),
        )

        response = client.complete(
            messages=[
                UserMessage(f"""Write a short review(up to 3 sentences for a user,
                                whose incomes equal float({incomes})
                                and expenses equal float({expenses}).
                                Your response must be addressed to the user.
                                Do not use any currencies in your response""")
            ],
            max_tokens=1000,
            model=model_name,
        )

        cleaned = re.sub(r'<think>.*?</think>',
                         '', response.choices[0].message.content,
                         flags=re.DOTALL).strip()
        result_queue.put(cleaned)
    except Exception as e:
        result_queue.put(f"Error: {e}")


def ai_review(incomes, expenses):
    result_queue = multiprocessing.Queue()
    process = multiprocessing.Process(target=_make_request, args=(incomes, expenses, result_queue))
    process.start()
    process.join(timeout=60)

    if process.is_alive():
        process.terminate()
        process.join()
        return "Unfortunately the AI assistant is too busy to analyze your accounts :("

    return result_queue.get()\
        if not result_queue.empty() \
        else "Unfortunately the AI assistant is too busy to analyze your accounts :("


if __name__ == "__main__":
    print(ai_review(1111, 777))
