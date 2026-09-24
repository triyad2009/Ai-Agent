import ctypes, json, os, shutil, subprocess, webbrowser
from datetime import datetime
from pathlib import Path
import mss, psutil, pyautogui

class ConfirmationRequired(Exception):
    def __init__(self,message): self.message=message

def expand(value): return Path(os.path.expandvars(os.path.expanduser(value))).resolve()

class ToolExecutor:
    def __init__(self,config):
        self.config=config
        self.roots=[expand(x) for x in config.get("allowed_roots",[])]
        self.logfile=Path("logs/agent.log"); self.logfile.parent.mkdir(exist_ok=True)
        self._skip_confirmation=False
        from tool_schemas import TOOL_SCHEMAS
        self.schemas=TOOL_SCHEMAS

    def log(self,action,args,result):
        with self.logfile.open("a",encoding="utf-8") as f:
            f.write(json.dumps({"time":datetime.now().isoformat(),"action":action,"args":args,"result":result},ensure_ascii=False)+"\n")

    def safe_path(self,path):
        target=expand(path)
        return any(target==root or root in target.parents for root in self.roots)

    def _needs_confirmation(self,name):
        return name in set(self.config.get("require_confirmation_for",[]))

    def _confirm_if_needed(self,name,message):
        if self._needs_confirmation(name) and not self._skip_confirmation: raise ConfirmationRequired(message)

    def execute(self,name,args,skip_confirmation=False):
        fn=getattr(self,name,None)
        if not fn:return {"ok":False,"error":"Unknown tool"}
        self._skip_confirmation=skip_confirmation
        try: result=fn(**args)
        finally: self._skip_confirmation=False
        self.log(name,args,result); return result

    def open_app(self,app):
        subprocess.Popen(app,shell=True); return {"ok":True,"message":f"Opened {app}"}

    def open_url(self,url):
        webbrowser.open(url); return {"ok":True,"message":f"Opened {url}"}

    def open_in_vscode(self,path):
        p=expand(path)
        if not self.safe_path(p):return {"ok":False,"error":"Path outside allowed roots"}
        subprocess.Popen(["code",str(p)]); return {"ok":True,"path":str(p),"message":"Opened in VS Code"}

    def list_files(self,path):
        p=expand(path)
        if not self.safe_path(p):return {"ok":False,"error":"Path outside allowed roots"}
        if not p.exists():return {"ok":False,"error":f"Path does not exist: {p}"}
        return {"ok":True,"files":[{"name":x.name,"path":str(x),"size":x.stat().st_size if x.is_file() else None} for x in p.iterdir()]}

    def read_file(self,path,max_chars=30000):
        p=expand(path)
        if not self.safe_path(p):return {"ok":False,"error":"Path outside allowed roots"}
        if not p.is_file():return {"ok":False,"error":"Not a file"}
        return {"ok":True,"path":str(p),"content":p.read_text(encoding="utf-8",errors="replace")[:max_chars]}

    def find_files(self,path,pattern="*"):
        p=expand(path)
        if not self.safe_path(p):return {"ok":False,"error":"Path outside allowed roots"}
        hits=[]
        for x in p.rglob(pattern):
            if len(hits)>=200:break
            hits.append({"path":str(x),"size":x.stat().st_size if x.is_file() else None})
        return {"ok":True,"files":hits}

    def largest_files(self,path,count=5):
        p=expand(path)
        if not self.safe_path(p):return {"ok":False,"error":"Path outside allowed roots"}
        files=[x for x in p.rglob("*") if x.is_file()]; files.sort(key=lambda x:x.stat().st_size,reverse=True)
        return {"ok":True,"files":[{"path":str(x),"size_bytes":x.stat().st_size} for x in files[:max(1,min(count,20))]]}

    def create_folder(self,path):
        p=expand(path)
        if not self.safe_path(p):return {"ok":False,"error":"Path outside allowed roots"}
        p.mkdir(parents=True,exist_ok=True); return {"ok":True,"path":str(p)}

    def write_file(self,path,content):
        self._confirm_if_needed("write_file",f"Create or replace this file?\n{path}")
        p=expand(path)
        if not self.safe_path(p):return {"ok":False,"error":"Path outside allowed roots"}
        p.parent.mkdir(parents=True,exist_ok=True); p.write_text(content,encoding="utf-8")
        return {"ok":True,"path":str(p),"bytes":len(content.encode("utf-8"))}

    def write_files(self,files):
        self._confirm_if_needed("write_files",f"Create or replace {len(files)} project files?")
        paths=[expand(x["path"]) for x in files]
        if any(not self.safe_path(p) for p in paths):return {"ok":False,"error":"One or more paths are outside allowed roots"}
        for item,p in zip(files,paths):
            p.parent.mkdir(parents=True,exist_ok=True); p.write_text(item["content"],encoding="utf-8")
        return {"ok":True,"files":[str(p) for p in paths]}

    def copy_file(self,source,destination):
        self._confirm_if_needed("copy_file",f"Copy {source} to {destination}?")
        s,d=expand(source),expand(destination)
        if not self.safe_path(s) or not self.safe_path(d):return {"ok":False,"error":"Path outside allowed roots"}
        shutil.copy2(s,d); return {"ok":True,"destination":str(d)}

    def move_file(self,source,destination):
        self._confirm_if_needed("move_file",f"Move {source} to {destination}?")
        s,d=expand(source),expand(destination)
        if not self.safe_path(s) or not self.safe_path(d):return {"ok":False,"error":"Path outside allowed roots"}
        shutil.move(s,d); return {"ok":True,"destination":str(d)}

    def rename_file(self,path,new_name):
        self._confirm_if_needed("rename_file",f"Rename {path} to {new_name}?")
        p=expand(path)
        if not self.safe_path(p):return {"ok":False,"error":"Path outside allowed roots"}
        dest=p.with_name(new_name); p.rename(dest); return {"ok":True,"path":str(dest)}

    def delete_file(self,path):
        self._confirm_if_needed("delete_file",f"Send {path} to the Windows Recycle Bin?")
        p=expand(path)
        if not self.safe_path(p):return {"ok":False,"error":"Path outside allowed roots"}
        flags=1|2|16
        class SHFILEOPSTRUCTW(ctypes.Structure):
            _fields_=[("hwnd",ctypes.c_void_p),("wFunc",ctypes.c_uint),("pFrom",ctypes.c_wchar_p),("pTo",ctypes.c_wchar_p),("fFlags",ctypes.c_ushort),("fAnyOperationsAborted",ctypes.c_bool),("hNameMappings",ctypes.c_void_p),("lpszProgressTitle",ctypes.c_wchar_p)]
        op=SHFILEOPSTRUCTW(0,3,str(p)+"\0",None,flags,False,None,None)
        result=ctypes.windll.shell32.SHFileOperationW(ctypes.byref(op))
        return {"ok":result==0,"message":"Sent to Recycle Bin" if result==0 else f"Recycle Bin operation failed: {result}"}

    def run_shell(self,command):
        self._confirm_if_needed("run_shell",f"Run PowerShell command?\n{command}")
        proc=subprocess.run(["powershell","-NoProfile","-Command",command],capture_output=True,text=True,timeout=self.config.get("max_shell_seconds",60))
        return {"ok":proc.returncode==0,"returncode":proc.returncode,"stdout":proc.stdout[-12000:],"stderr":proc.stderr[-12000:]}

    def start_dev_server(self,command,cwd):
        self._confirm_if_needed("start_dev_server",f"Start a development server?\n{command}\nDirectory: {cwd}")
        p=expand(cwd)
        if not self.safe_path(p):return {"ok":False,"error":"Directory outside allowed roots"}
        proc=subprocess.Popen(command,cwd=str(p),shell=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        return {"ok":True,"pid":proc.pid,"message":f"Development server started with PID {proc.pid}"}

    def screenshot(self,path="screenshots/screen.png"):
        p=expand(path); p.parent.mkdir(parents=True,exist_ok=True)
        with mss.mss() as sct:sct.shot(output=str(p))
        return {"ok":True,"path":str(p)}

    def system_info(self):
        return {"ok":True,"platform":"Windows","cpu_percent":psutil.cpu_percent(interval=.2),"memory_percent":psutil.virtual_memory().percent}

    def keyboard_write(self,text):
        self._confirm_if_needed("keyboard_write",f"Type this text?\n{text[:200]}")
        if not self.config.get("enable_mouse_keyboard",True):return {"ok":False,"error":"Disabled in config"}
        pyautogui.write(text,interval=.01); return {"ok":True}

    def mouse_click(self,x,y,button="left"):
        self._confirm_if_needed("mouse_click",f"Click at ({x}, {y}) with {button}?")
        if not self.config.get("enable_mouse_keyboard",True):return {"ok":False,"error":"Disabled in config"}
        pyautogui.click(x,y,button=button); return {"ok":True}
