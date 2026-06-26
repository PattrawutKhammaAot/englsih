#!/usr/bin/env python3
"""Local static + AI API proxy server (fixes CORS for MaxPlus, Groq, etc.)."""
import base64
import http.server
import io
import json
import os
import socket
import socketserver
import ssl
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CERT = ROOT / "cert.pem"
KEY = ROOT / "key.pem"
DEFAULT_HTTPS_PORT = 8443
DEFAULT_HTTP_PORT = 8080
MAX_PORT_TRIES = 10


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


def get_ipv4():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "127.0.0.1"


def find_openssl():
    for cmd in (
        "openssl",
        r"C:\Program Files\Git\usr\bin\openssl.exe",
        r"C:\Program Files (x86)\Git\usr\bin\openssl.exe",
    ):
        try:
            subprocess.run([cmd, "version"], check=True, capture_output=True)
            return cmd
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue
    return None


def make_cert():
    ip = get_ipv4()
    openssl = find_openssl()
    if not openssl:
        print("\n[ERROR] OpenSSL not found — install Git for Windows")
        sys.exit(1)
    san = f"subjectAltName=DNS:localhost,IP:127.0.0.1,IP:{ip}"
    subprocess.run(
        [
            openssl,
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-keyout",
            str(KEY),
            "-out",
            str(CERT),
            "-days",
            "3650",
            "-nodes",
            "-subj",
            "/CN=learning-english-local",
            "-addext",
            san,
        ],
        check=True,
    )
    print(f"Certificate created (IP: {ip})")


def gemini_contents(messages):
    contents = []
    for m in messages:
        role = "model" if m.get("role") == "assistant" else "user"
        if contents and contents[-1]["role"] == role:
            contents[-1]["parts"][0]["text"] += "\n\n" + m["content"]
        else:
            contents.append({"role": role, "parts": [{"text": m["content"]}]})
    if contents and contents[0]["role"] == "model":
        contents.insert(
            0,
            {"role": "user", "parts": [{"text": "Let's continue our English lesson."}]},
        )
    return contents


def extract_text(fmt, data):
    if fmt == "anthropic":
        return (data.get("content") or [{}])[0].get("text") or ""
    if fmt == "gemini":
        candidates = data.get("candidates") or []
        if candidates:
            parts = candidates[0].get("content", {}).get("parts") or []
            if parts:
                return parts[0].get("text") or ""
        return ""
    choices = data.get("choices") or []
    if choices:
        return choices[0].get("message", {}).get("content") or ""
    return ""


def error_message(data, status):
    err = data.get("error")
    if isinstance(err, dict):
        return err.get("message") or str(err)
    if isinstance(err, str):
        return err
    return data.get("message") or f"HTTP {status}"


DEFAULT_UA = "Mozilla/5.0 (compatible; LearningEnglish-Tutor/1.0)"


def api_headers(extra=None):
    headers = {"User-Agent": DEFAULT_UA, "Accept": "application/json"}
    if extra:
        headers.update(extra)
    return headers


def multipart_encode(fields, files):
    boundary = "----LEBoundary" + os.urandom(8).hex()
    body = io.BytesIO()
    for name, value in fields.items():
        body.write(f"--{boundary}\r\n".encode())
        body.write(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        body.write(f"{value}\r\n".encode())
    for name, (filename, content, content_type) in files.items():
        body.write(f"--{boundary}\r\n".encode())
        body.write(
            f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode()
        )
        body.write(f"Content-Type: {content_type}\r\n\r\n".encode())
        body.write(content)
        body.write(b"\r\n")
    body.write(f"--{boundary}--\r\n".encode())
    return boundary, body.getvalue()


def proxy_transcribe(body):
    audio_b64 = body.get("audio") or ""
    mime = body.get("mimeType") or "audio/webm"
    base_url = (body.get("baseUrl") or "").rstrip("/")
    api_key = body.get("apiKey") or ""
    model = body.get("model") or "whisper-large-v3-turbo"
    language = body.get("language") or "en"

    if not base_url or not api_key or not audio_b64:
        return 400, {"error": {"message": "Missing baseUrl, apiKey, or audio"}}

    try:
        audio_bytes = base64.b64decode(audio_b64)
    except Exception as exc:
        return 400, {"error": {"message": f"Invalid audio data: {exc}"}}

    ext = "webm" if "webm" in mime else "wav"
    fields = {"model": model, "language": language, "response_format": "json"}
    files = {"file": (f"audio.{ext}", audio_bytes, mime)}
    boundary, payload = multipart_encode(fields, files)

    url = base_url + "/v1/audio/transcriptions"
    req = urllib.request.Request(
        url,
        data=payload,
        headers=api_headers(
            {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            }
        ),
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return resp.status, data
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {"error": {"message": raw or exc.reason}}
        return exc.code, data


def proxy_ai(body):
    fmt = body.get("format", "openai")
    base_url = (body.get("baseUrl") or "").rstrip("/")
    api_key = body.get("apiKey") or ""
    model = body.get("model") or ""
    system = body.get("system") or ""
    messages = body.get("messages") or []
    provider_id = body.get("providerId") or ""
    referer = body.get("referer") or "http://localhost"

    if not base_url or not api_key or not model:
        return 400, {"error": {"message": "Missing baseUrl, apiKey, or model"}}

    headers = api_headers({"Content-Type": "application/json"})

    if fmt == "anthropic":
        url = base_url + "/v1/messages"
        headers["x-api-key"] = api_key
        headers["anthropic-version"] = "2023-06-01"
        if provider_id != "anthropic":
            headers["Authorization"] = f"Bearer {api_key}"
        payload = {
            "model": model,
            "max_tokens": 1500,
            "system": system,
            "messages": messages,
        }
    elif fmt == "gemini":
        url = (
            f"{base_url}/v1beta/models/{urllib.request.quote(model, safe='')}"
            f":generateContent?key={urllib.request.quote(api_key, safe='')}"
        )
        payload = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": gemini_contents(messages),
            "generationConfig": {"maxOutputTokens": 1500},
        }
    else:
        url = base_url + "/v1/chat/completions"
        headers["Authorization"] = f"Bearer {api_key}"
        if fmt == "openrouter":
            headers["HTTP-Referer"] = referer
            headers["X-Title"] = "AI English Tutor"
        payload = {
            "model": model,
            "max_tokens": 1500,
            "messages": [{"role": "system", "content": system}] + messages,
        }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return resp.status, data
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {"error": {"message": raw or exc.reason}}
        return exc.code, data


class LearningEnglishHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, fmt, *args):
        if self.path.startswith("/api/"):
            sys.stderr.write("%s - [%s] %s\n" % (self.address_string(), self.log_date_time_string(), fmt % args))

    def do_GET(self):
        path = self.path.split("?", 1)[0].rstrip("/")
        if path == "/api/health":
            self.handle_health()
        else:
            super().do_GET()

    def handle_health(self):
        out = {"ok": True, "proxy": True, "transcribe": True}
        payload = json.dumps(out).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self):
        path = self.path.split("?", 1)[0].rstrip("/")
        if path in ("/api/proxy", "/api/transcribe", "/api/health"):
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()
        else:
            super().do_OPTIONS()

    def do_POST(self):
        path = self.path.split("?", 1)[0].rstrip("/")
        if path == "/api/proxy":
            self.handle_proxy()
        elif path == "/api/transcribe":
            self.handle_transcribe()
        else:
            self.send_error(404)

    def handle_proxy(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length).decode("utf-8"))
            status, data = proxy_ai(body)
            fmt = body.get("format", "openai")
            if status >= 400:
                out = {
                    "ok": False,
                    "status": status,
                    "message": error_message(data, status),
                }
            else:
                out = {"ok": True, "status": status, "text": extract_text(fmt, data)}
        except Exception as exc:
            out = {"ok": False, "status": 500, "message": str(exc)}

        payload = json.dumps(out).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def handle_transcribe(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length).decode("utf-8"))
            status, data = proxy_transcribe(body)
            if status >= 400:
                out = {
                    "ok": False,
                    "status": status,
                    "message": error_message(data, status),
                }
            else:
                out = {"ok": True, "status": status, "text": data.get("text") or ""}
        except Exception as exc:
            out = {"ok": False, "status": 500, "message": str(exc)}

        payload = json.dumps(out).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def bind_server(start_port):
    last_err = None
    for port in range(start_port, start_port + MAX_PORT_TRIES):
        try:
            httpd = ReusableTCPServer(("0.0.0.0", port), LearningEnglishHandler)
            return httpd, port
        except OSError as err:
            last_err = err
            if getattr(err, "winerror", None) == 10048 or err.errno in (98, 10048):
                print(f"  Port {port} in use, trying {port + 1}...")
                continue
            raise
    print(f"\n[ERROR] Ports {start_port}-{start_port + MAX_PORT_TRIES - 1} all in use")
    print("  Close other server windows (Ctrl+C) then retry")
    if last_err:
        print(f"  Last error: {last_err}")
    sys.exit(1)


def run(use_https):
    os.chdir(ROOT)
    default_port = DEFAULT_HTTPS_PORT if use_https else DEFAULT_HTTP_PORT
    if use_https and (not CERT.exists() or not KEY.exists()):
        make_cert()

    httpd, port = bind_server(default_port)

    if use_https:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(str(CERT), str(KEY))
        httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
        scheme = "https"
    else:
        scheme = "http"

    ip = get_ipv4()
    print()
    print("=" * 48)
    print("  Learning English - Local Server + AI Proxy")
    print("=" * 48)
    print(f"  This PC:     {scheme}://localhost:{port}/ai.html")
    print(f"  Other WiFi:  {scheme}://{ip}:{port}/ai.html")
    if port != default_port:
        print(f"  (Port {default_port} was busy — using {port})")
    print()
    print("  AI Proxy: /api/proxy (MaxPlus, Groq, OpenRouter OK)")
    print("  Whisper:  /api/transcribe (Voice mode — Groq/OpenAI)")
    if use_https:
        print("  First visit: Advanced -> Proceed (self-signed cert)")
        print("  Mic: Allow while visiting the site (once)")
    print("  Stop: Ctrl+C")
    print("=" * 48)
    print()
    httpd.serve_forever()


def main():
    use_https = "--https" in sys.argv or "-s" in sys.argv
    run(use_https)


if __name__ == "__main__":
    main()
