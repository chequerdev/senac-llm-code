import json
import os
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from dotenv import load_dotenv
from openai import APIConnectionError, AuthenticationError, OpenAI, RateLimitError


ROOT = Path(__file__).resolve().parent
WEB_DIR = ROOT / "chatbot-web"

load_dotenv(ROOT.parent / ".env")

client = OpenAI(
    base_url=os.environ.get("LLM_BASE_URL", "https://api.mistral.ai/v1"),
    api_key=os.environ.get("OPENAI_API_KEY"),
)
MODELO = os.environ.get("LLM_MODELO", "mistral-small-latest")

SYSTEM_PROMPT = (
    "Você é um assistente útil, amigável e super gente boa. "
    "Você entende muito de carros e explica assuntos automotivos "
    "de forma simples, prática e descontraída."
)

conversations: dict[str, list[dict[str, str]]] = {}
conversations_lock = threading.Lock()


class ChatHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send_file(WEB_DIR / "index.html", "text/html; charset=utf-8")
        elif self.path == "/styles.css":
            self._send_file(WEB_DIR / "styles.css", "text/css; charset=utf-8")
        elif self.path == "/app.js":
            self._send_file(WEB_DIR / "app.js", "text/javascript; charset=utf-8")
        else:
            self._send_json(404, {"error": "Página não encontrada."})

    def do_POST(self):
        if self.path == "/api/chat":
            self._chat()
        elif self.path == "/api/reset":
            self._reset()
        else:
            self._send_json(404, {"error": "Rota não encontrada."})

    def _chat(self):
        data = self._read_json()
        if data is None:
            return

        message = str(data.get("message", "")).strip()
        session_id = str(data.get("session_id", "")).strip() or str(uuid.uuid4())

        if not message:
            self._send_json(400, {"error": "Digite uma mensagem."})
            return
        if len(message) > 4000:
            self._send_json(400, {"error": "A mensagem deve ter no máximo 4.000 caracteres."})
            return

        with conversations_lock:
            messages = conversations.setdefault(
                session_id,
                [{"role": "system", "content": SYSTEM_PROMPT}],
            )
            messages.append({"role": "user", "content": message})
            request_messages = list(messages)

        try:
            response = client.chat.completions.create(
                model=MODELO,
                messages=request_messages,
            )
            answer = response.choices[0].message.content or "Não recebi uma resposta em texto."
        except AuthenticationError:
            self._rollback_user_message(session_id)
            self._send_json(401, {"error": "A chave da API foi recusada. Confira o arquivo .env."})
            return
        except RateLimitError:
            self._rollback_user_message(session_id)
            self._send_json(429, {"error": "A API está sem cota ou atingiu o limite. Confira o plano e tente novamente."})
            return
        except APIConnectionError:
            self._rollback_user_message(session_id)
            self._send_json(503, {"error": "Não foi possível conectar à API. Confira sua internet e o endpoint."})
            return
        except Exception as error:
            self._rollback_user_message(session_id)
            print(f"Erro ao consultar o modelo: {error}")
            self._send_json(500, {"error": "Ocorreu um erro ao gerar a resposta."})
            return

        with conversations_lock:
            conversations[session_id].append({"role": "assistant", "content": answer})

        self._send_json(200, {"answer": answer, "session_id": session_id, "model": MODELO})

    def _reset(self):
        data = self._read_json()
        if data is None:
            return
        session_id = str(data.get("session_id", "")).strip()
        if session_id:
            with conversations_lock:
                conversations.pop(session_id, None)
        self._send_json(200, {"ok": True})

    def _rollback_user_message(self, session_id):
        with conversations_lock:
            messages = conversations.get(session_id, [])
            if messages and messages[-1].get("role") == "user":
                messages.pop()

    def _read_json(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            return json.loads(self.rfile.read(length) or b"{}")
        except (ValueError, json.JSONDecodeError):
            self._send_json(400, {"error": "JSON inválido."})
            return None

    def _send_file(self, path, content_type):
        if not path.is_file():
            self._send_json(404, {"error": "Arquivo não encontrado."})
            return
        content = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(content)

    def _send_json(self, status, payload):
        content = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {format % args}")


if __name__ == "__main__":
    host = "127.0.0.1"
    port = int(os.environ.get("CHATBOT_PORT", "8000"))
    server = ThreadingHTTPServer((host, port), ChatHandler)
    print(f"Chatbot web rodando em http://{host}:{port}")
    print("Pressione Ctrl+C para encerrar.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor encerrado.")
    finally:
        server.server_close()
