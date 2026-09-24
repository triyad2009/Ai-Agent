import json, os, threading, uuid
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory
from dotenv import load_dotenv
from agent import WindowsAgent, ConfirmationRequired

load_dotenv()
BASE = Path(__file__).resolve().parent
STATIC = BASE / "web"
CONFIG = json.loads((BASE / "config.json").read_text(encoding="utf-8"))

app = Flask(__name__, static_folder=str(STATIC), static_url_path="")
sessions = {}
lock = threading.Lock()

def get_agent(session_id):
    with lock:
        if session_id not in sessions:
            sessions[session_id] = WindowsAgent(CONFIG)
        return sessions[session_id]

@app.get("/")
def index():
    return send_from_directory(STATIC, "index.html")

@app.get("/<path:path>")
def static_file(path):
    return send_from_directory(STATIC, path)

@app.post("/api/session")
def create_session():
    sid = uuid.uuid4().hex
    get_agent(sid)
    return jsonify({"session_id": sid})

@app.post("/api/chat")
def chat():
    data = request.get_json(force=True) or {}
    prompt = (data.get("message") or "").strip()
    sid = data.get("session_id")
    if not prompt:
        return jsonify({"ok": False, "error": "Message is required"}), 400
    if not sid:
        sid = uuid.uuid4().hex
    agent = get_agent(sid)
    try:
        result = agent.run(prompt)
        return jsonify({"ok": True, "session_id": sid, **result})
    except Exception as exc:
        return jsonify({"ok": False, "session_id": sid, "error": str(exc)}), 500

@app.post("/api/confirm")
def confirm():
    data = request.get_json(force=True) or {}
    sid = data.get("session_id")
    approved = bool(data.get("approved"))
    if not sid or sid not in sessions:
        return jsonify({"ok": False, "error": "Session not found"}), 404
    try:
        result = sessions[sid].resolve_confirmation(approved)
        return jsonify({"ok": True, "session_id": sid, **result})
    except Exception as exc:
        return jsonify({"ok": False, "session_id": sid, "error": str(exc)}), 500

@app.get("/api/health")
def health():
    return jsonify({"ok": True, "service": "AI-Agent", "voice": "browser Web Speech API"})

if __name__ == "__main__":
    host = os.getenv("AGENT_HOST", "127.0.0.1")
    port = int(os.getenv("AGENT_PORT", "3000"))
    print(f"AI-Agent web console: http://{host}:{port}")
    app.run(host=host, port=port, threaded=True, debug=False)
