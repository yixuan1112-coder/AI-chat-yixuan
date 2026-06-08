import json
import mimetypes
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib import error, request


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


def call_ai(message):
    api_key = os.getenv("AI_API_KEY")
    api_url = os.getenv("AI_API_URL")
    model = os.getenv("AI_MODEL", "deepseek-chat")

    if not api_key or not api_url:
        return (
            "AI 后端已经连通，但还没有配置 AI_API_KEY 和 AI_API_URL。\n\n"
            "你可以先这样测试前端窗口是否工作。接入真实模型时，在项目根目录新建 .env，"
            "写入 AI_API_KEY、AI_API_URL、AI_MODEL，然后重新运行 python app.py。"
        )

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are the BatteryTwin project assistant. Answer in the user's language. "
                    "Help with battery datasets, schema, ETL scripts, quality checks, and benchmark workflows. "
                    "Use the project context below when it is relevant.\n\n"
                    f"{PROJECT_CONTEXT}"
                ),
            },
            {"role": "user", "content": message},
        ],
        "temperature": 0.3,
    }
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        api_url,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"AI API error {exc.code}: {detail}") from exc
    except Exception as exc:
        raise RuntimeError(f"AI API request failed: {exc}") from exc

    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Unexpected AI API response: {data}") from exc


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
                self.send_json({"reply": "请输入一个问题。"}, status=400)
                return
            reply = call_ai(message)
            self.send_json({"reply": reply})
        except Exception as exc:
            self.send_json({"reply": f"AI 后端出错：{exc}"}, status=500)

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
