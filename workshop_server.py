"""Servidor de aprendizaje local. No tiene operaciones cloud ni acceso a credenciales."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
from urllib.parse import urlparse
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from tutor import clean_text, mock_answer


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Evitar registrar preguntas, identificadores o datos enviados en URL.
        pass

    def send(self, status, content, kind="application/json; charset=utf-8"):
        payload = content if isinstance(content, bytes) else json.dumps(content, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        path = urlparse(self.path).path
        files = {
            "/": (ROOT / "web/index.html", "text/html; charset=utf-8"),
            "/style.css": (ROOT / "web/style.css", "text/css; charset=utf-8"),
            "/app.js": (ROOT / "web/app.js", "text/javascript; charset=utf-8"),
            "/guia.md": (ROOT / "docs/taller.md", "text/markdown; charset=utf-8"),
            "/capturas.json": (ROOT / "web/capturas.json", "application/json; charset=utf-8"),
            "/evidencias.json": (ROOT / "web/evidencias.json", "application/json; charset=utf-8"),
            "/Alexa-Bedrock-Taller.zip": (ROOT / "output/Alexa-Bedrock-Taller.zip", "application/zip"),
        }
        for name in ["taller.md", "uso-limites.md", "costos-y-alternativas.md", "certificacion.md", "capturas.md"]:
            files["/" + name] = (ROOT / "docs" / name, "text/markdown; charset=utf-8")
        if path in files:
            target, mime = files[path]
            return self.send(200, target.read_bytes(), mime) if target.is_file() else self.send(404, {"error": "Archivo aun no disponible"})
        if path.startswith("/capturas/") and path.endswith(".jpg"):
            target = (ROOT / "docs" / path.lstrip("/")).resolve()
            if target.is_relative_to((ROOT / "docs/capturas").resolve()) and target.is_file():
                return self.send(200, target.read_bytes(), "image/jpeg")
        if path == "/api/status":
            evidence = ROOT / "output/evidence/local-tests.json"
            passed = json.loads(evidence.read_text(encoding="utf-8")).get("passed") if evidence.exists() else None
            return self.send(200, {"mode": "local-simulation", "local_tests_passed": passed, "cloud": "requires-your-own-account", "device": "pending", "certification": "pending"})
        return self.send(404, {"error": "Ruta no disponible"})

    def do_POST(self):
        origin = self.headers.get("Origin")
        expected = "http://127.0.0.1:" + str(self.server.server_port)
        if origin and origin != expected:
            return self.send(403, {"error": "Origen no permitido"})
        if self.path != "/api/simulate" or self.headers.get("Content-Type") != "application/json":
            return self.send(400, {"error": "Solicitud no valida"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 12000:
                raise ValueError()
            data = json.loads(self.rfile.read(length))
            question = clean_text(data.get("question"), 600)
            history = data.get("history", [])
            if not question or not isinstance(history, list):
                raise ValueError()
            safe_history = [item for item in history[-3:] if isinstance(item, dict) and isinstance(item.get("question"), str) and isinstance(item.get("answer"), str)]
            return self.send(200, {"answer": mock_answer(question, safe_history), "mode": "simulation", "aws_calls": 0})
        except (ValueError, TypeError, AttributeError):
            return self.send(400, {"error": "Pregunta o historial no valido"})


def serve(port=8092):
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print("Taller: http://127.0.0.1:" + str(server.server_port), flush=True)
    print("Simulacion local. No consume AWS ni prueba la skill real. Ctrl+C para cerrar.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
