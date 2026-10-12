
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url=os.environ.get("LLM_BASE_URL", "https://api.mistral.ai/v1"),
    api_key=os.environ.get("OPENAI_API_KEY"),
)
MODELO = os.environ.get("LLM_MODELO", "mistral-small-latest")

response = client.chat.completions.create(
    model=MODELO,
    messages=[
        {"role": "user", "content": "Por que o céu é azul?"},
    ],
)
print(response.choices[0].message.content)
