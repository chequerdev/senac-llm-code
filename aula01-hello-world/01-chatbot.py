import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url=os.environ.get("LLM_BASE_URL", "https://api.mistral.ai/v1"),
    api_key=os.environ.get("OPENAI_API_KEY"),
)
MODELO = os.environ.get("LLM_MODELO", "mistral-small-latest")


messages = [
    {"role": "system", "content": "Você é um assistente virtual útil e amigável, super gente boa e manja muito sobre carros... "},
    {"role": "user", "content": "Olá!"},
]

# Primeira resposta do bot
response = client.chat.completions.create(model=MODELO, messages=messages)
print("Bot:", response.choices[0].message.content)

# Continua a conversa:
while True:
    user_input = input("Usuário: ")
    if not user_input:
        break  # sai do loop quando a entrada é vazia
    # pode adicionar mais mensagens como contexto
    messages.append({"role": "user", "content": user_input})
    response = client.chat.completions.create(model=MODELO, messages=messages)
    answer = response.choices[0].message.content
    print("Bot:", answer)
    messages.append({"role": "assistant", "content": answer})
