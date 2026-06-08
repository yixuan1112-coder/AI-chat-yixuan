import json
import mimetypes
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib import error, parse, request


ROOT = Path(__file__).resolve().parent
HOST = "127.0.0.1"
PORT = int(os.getenv("PORT", "8000"))


def load_dotenv():
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def load_project_context():
    parts = []
    for relative_path in [
        "README.md",
        "README_EN.md",
        "docs/schema/schema_overview.md",
        "dataset_registry.csv",
    ]:
        path = ROOT / relative_path
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        parts.append(f"[{relative_path}]\n{text[:3500]}")
    return "\n\n".join(parts)


load_dotenv()
PROJECT_CONTEXT = load_project_context()


def build_system_prompt():
    return (
        "You are the BatteryTwin project assistant. Answer in the user's language. "
        "Help with battery datasets, schema, ETL scripts, quality checks, and benchmark workflows. "
        "Use the project context below when it is relevant.\n\n"
        f"{PROJECT_CONTEXT}"
    )


def post_json(url, payload, headers):
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"AI API error {exc.code}: {detail}") from exc
    except Exception as exc:
        raise RuntimeError(f"AI API request failed: {exc}") from exc


def call_openai_compatible(message):
    api_key = os.getenv("AI_API_KEY")
    api_url = os.getenv("AI_API_URL")
    model = os.getenv("AI_MODEL", "deepseek-chat")

    if not api_key or not api_url:
        return (
            "The AI backend is connected, but AI_API_KEY and AI_API_URL are not configured yet.\n\n"
            "You can use this message to confirm that the chat window is working. To connect a real model, "
            "create a .env file in the project root, add AI_API_KEY, AI_API_URL, and AI_MODEL, then restart python app.py."
        )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": build_system_prompt()},
            {"role": "user", "content": message},
        ],
        "temperature": 0.3,
    }
    data = post_json(api_url, payload, {"Authorization": f"Bearer {api_key}"})

    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Unexpected AI API response: {data}") from exc


def call_gemini(message):
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("AI_API_KEY")
    model = os.getenv("GEMINI_MODEL") or os.getenv("AI_MODEL", "gemini-2.5-flash")
    api_url = os.getenv("GEMINI_API_URL")

    if not api_url:
        encoded_model = parse.quote(model, safe="")
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{encoded_model}:generateContent"

    if not api_key:
        return (
            "The Gemini backend is connected, but GEMINI_API_KEY is not configured yet.\n\n"
            "Create a .env file in the project root, add GEMINI_API_KEY, then restart python app.py."
        )

    payload = {
        "systemInstruction": {
            "parts": [{"text": build_system_prompt()}],
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": message}],
            }
        ],
        "generationConfig": {
            "temperature": 0.3,
        },
    }
    data = post_json(api_url, payload, {"x-goog-api-key": api_key})

    try:
        parts = data["candidates"][0]["content"]["parts"]
        return "".join(part.get("text", "") for part in parts).strip() or "Gemini did not return any text content."
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Unexpected Gemini API response: {data}") from exc


def call_ai(message):
    provider = os.getenv("AI_PROVIDER", "").strip().lower()
    if not provider and os.getenv("GEMINI_API_KEY"):
        provider = "gemini"
    if provider == "gemini":
        return call_gemini(message)
    return call_openai_compatible(message)


class BatteryTwinHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        if self.path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        if self.path != "/api/chat":
            self.send_error(404, "Not found")
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(length).decode("utf-8")
            payload = json.loads(raw_body or "{}")
            message = str(payload.get("message", "")).strip()
            if not message:
                self.send_json({"reply": "Please enter a question."}, status=400)
                return
            reply = call_ai(message)
            self.send_json({"reply": reply})
        except Exception as exc:
            self.send_json({"reply": f"AI backend error: {exc}"}, status=500)

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    mimetypes.add_type("text/html; charset=utf-8", ".html")
    server = ThreadingHTTPServer((HOST, PORT), BatteryTwinHandler)
    print(f"BatteryTwin AI server running at http://{HOST}:{PORT}/")
    server.serve_forever()
