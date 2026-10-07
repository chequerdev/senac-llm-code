# Chatão web

Na raiz do projeto, inicie o servidor:

```powershell
.\.venv\Scripts\python.exe .\aula01-hello-world\02-chatbot-web.py
```

Depois acesse [http://127.0.0.1:8000](http://127.0.0.1:8000).

O backend lê `OPENAI_API_KEY`, `LLM_BASE_URL` e `LLM_MODELO` do arquivo
`.env` na raiz. A chave nunca é enviada ao navegador.

Para encerrar o servidor, pressione `Ctrl+C` no terminal.
