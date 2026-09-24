import ctypes, json, os, shutil, subprocess, webbrowser
from datetime import datetime
from pathlib import Path
import mss
import psutil
import pyautogui

class _SHFILEOPSTRUCTW(ctypes.Structure):
    _fields_ = [
        ("hwnd", ctypes.c_void_p), ("wFunc", ctypes.c_uint),
        ("pFrom", ctypes.c_wchar_p), ("pTo", ctypes.c_wchar_p),
        ("fFlags", ctypes.c_ushort), ("fAnyOperationsAborted", ctypes.c_bool),
        ("hNameMappings", ctypes.c_void_p), ("lpszProgressTitle", ctypes.c_wchar_p)
    ]

def expand(value):
    return Path(os.path.expandvars(os.path.expanduser(value))).resolve()

class ToolExecutor:
    def __init__(self, config):
        self.config = config
        self.roots = [expand(x) for x in config.get("allowed_roots", [])]
        self.logfile = Path("logs/agent.log")
        self.logfile.parent.mkdir(exist_ok=True)

    def log(self, action, args, result):
        with self.logfile.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"time": datetime.now().isoformat(), "action": action, "args": args, "result": result}, ensure_ascii=False) + "\n")

    def safe_path(self, path):
        target = expand(path)
        return any(target == root or root in target.parents for root in self.roots)

    def confirm(self, message):
        return input(f"\nCONFIRM: {message} [y/N] ").strip().lower() in {"y", "yes"}

    def execute(self, name, args):
        fn = getattr(self, name, None)
        if not fn:
            return {"ok": False, "error": "Unknown tool"}
        try:
            result = fn(**args)
        except Exception as exc:
            result = {"ok": False, "error": str(exc)}
        self.log(name, args, result)
        return result

    def open_app(self, app):
        subprocess.Popen(app, shell=True)
        return {"ok": True, "message": f"Opened {app}"}

    def open_url(self, url):
        webbrowser.open(url)
        return {"ok": True, "message": f"Opened {url}"}

    def list_files(self, path):
        p = expand(path)
        if not self.safe_path(p): return {"ok": False, "error": "Path outside allowed roots"}
        return {"ok": True, "files": [{"name": x.name, "path": str(x), "size": x.stat().st_size if x.is_file() else None} for x in p.iterdir()]}

    def find_files(self, path, pattern="*"):
        p = expand(path)
        if not self.safe_path(p): return {"ok": False, "error": "Path outside allowed roots"}
        hits = []
        for x in p.rglob(pattern):
            if len(hits) >= 200: break
            hits.append({"path": str(x), "size": x.stat().st_size if x.is_file() else None})
        return {"ok": True, "files": hits}

    def largest_files(self, path, count=5):
        p = expand(path)
        if not self.safe_path(p): return {"ok": False, "error": "Path outside allowed roots"}
        files = [x for x in p.rglob("*") if x.is_file()]
        files.sort(key=lambda x: x.stat().st_size, reverse=True)
        return {"ok": True, "files": [{"path": str(x), "size_bytes": x.stat().st_size} for x in files[:max(1, min(count, 20))]]}

    def create_folder(self, path):
        p = expand(path)
        if not self.safe_path(p): return {"ok": False, "error": "Path outside allowed roots"}
        p.mkdir(parents=True, exist_ok=True)
        return {"ok": True, "path": str(p)}

    def copy_file(self, source, destination):
        if not self.confirm(f"Copy {source} to {destination}?"): return {"ok": False, "cancelled": True}
        s, d = expand(source), expand(destination)
        if not self.safe_path(s) or not self.safe_path(d): return {"ok": False, "error": "Path outside allowed roots"}
        shutil.copy2(s, d)
        return {"ok": True, "destination": str(d)}

    def move_file(self, source, destination):
        if not self.confirm(f"Move {source} to {destination}?"): return {"ok": False, "cancelled": True}
        s, d = expand(source), expand(destination)
        if not self.safe_path(s) or not self.safe_path(d): return {"ok": False, "error": "Path outside allowed roots"}
        shutil.move(s, d)
        return {"ok": True, "destination": str(d)}

    def rename_file(self, path, new_name):
        if not self.confirm(f"Rename {path} to {new_name}?"): return {"ok": False, "cancelled": True}
        p = expand(path)
        if not self.safe_path(p): return {"ok": False, "error": "Path outside allowed roots"}
        dest = p.with_name(new_name)
        p.rename(dest)
        return {"ok": True, "path": str(dest)}

    def delete_file(self, path):
        if not self.confirm(f"Send {path} to the Recycle Bin?"): return {"ok": False, "cancelled": True}
        p = expand(path)
        if not self.safe_path(p): return {"ok": False, "error": "Path outside allowed roots"}
        flags = 0x00000001 | 0x00000002 | 0x00000010
        op = _SHFILEOPSTRUCTW(0, 3, str(p) + "\0", None, flags, False, None, None)
        result = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(op))
        return {"ok": result == 0, "message": "Sent to Recycle Bin" if result == 0 else f"Recycle Bin operation failed: {result}"}

    def run_shell(self, command):
        if not self.confirm(f"Run PowerShell command: {command}"): return {"ok": False, "cancelled": True}
        proc = subprocess.run(["powershell", "-NoProfile", "-Command", command], capture_output=True, text=True, timeout=self.config.get("max_shell_seconds", 30))
        return {"ok": proc.returncode == 0, "returncode": proc.returncode, "stdout": proc.stdout[-12000:], "stderr": proc.stderr[-12000:]}

    def screenshot(self, path="screenshots/screen.png"):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with mss.mss() as sct: sct.shot(output=path)
        return {"ok": True, "path": str(Path(path).resolve())}

    def system_info(self):
        return {"ok": True, "platform": "Windows", "cpu_percent": psutil.cpu_percent(interval=0.2), "memory_percent": psutil.virtual_memory().percent}

    def keyboard_write(self, text):
        if not self.config.get("enable_mouse_keyboard", True): return {"ok": False, "error": "Disabled in config"}
        if not self.confirm(f"Type this text: {text[:120]}"): return {"ok": False, "cancelled": True}
        pyautogui.write(text, interval=0.01)
        return {"ok": True}

    def mouse_click(self, x, y, button="left"):
        if not self.config.get("enable_mouse_keyboard", True): return {"ok": False, "error": "Disabled in config"}
        if not self.confirm(f"Click at ({x}, {y}) with {button}?"): return {"ok": False, "cancelled": True}
        pyautogui.click(x, y, button=button)
        return {"ok": True}
