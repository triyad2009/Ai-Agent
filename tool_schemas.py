def f(name,description,properties,required):
    return {"type":"function","name":name,"description":description,"parameters":{"type":"object","properties":properties,"required":required,"additionalProperties":False}}
STR={"type":"string"}; PATH={"type":"string"}; NUM={"type":"number"}
FILE_ITEM={"type":"object","properties":{"path":PATH,"content":STR},"required":["path","content"],"additionalProperties":False}
TOOL_SCHEMAS=[
f("open_app","Open a Windows application or executable.",{"app":STR},["app"]),
f("open_url","Open a URL in the default browser.",{"url":STR},["url"]),
f("open_in_vscode","Open a project/file in VS Code.",{"path":PATH},["path"]),
f("list_files","List files and folders.",{"path":PATH},["path"]),
f("read_file","Read a text file.",{"path":PATH,"max_chars":{"type":"integer","minimum":1000,"maximum":50000}},["path"]),
f("find_files","Recursively find files using a glob pattern.",{"path":PATH,"pattern":STR},["path","pattern"]),
f("largest_files","Find the largest files.",{"path":PATH,"count":{"type":"integer","minimum":1,"maximum":20}},["path"]),
f("create_folder","Create a folder.",{"path":PATH},["path"]),
f("write_file","Create or replace one text file. Requires confirmation.",{"path":PATH,"content":STR},["path","content"]),
f("write_files","Create or replace multiple project files with one confirmation.",{"files":{"type":"array","items":FILE_ITEM,"minItems":1,"maxItems":80}},["files"]),
f("copy_file","Copy a file. Requires confirmation.",{"source":PATH,"destination":PATH},["source","destination"]),
f("move_file","Move a file. Requires confirmation.",{"source":PATH,"destination":PATH},["source","destination"]),
f("rename_file","Rename a file/folder. Requires confirmation.",{"path":PATH,"new_name":STR},["path","new_name"]),
f("delete_file","Send a file to Recycle Bin. Requires confirmation.",{"path":PATH},["path"]),
f("run_shell","Run a PowerShell command. Requires confirmation.",{"command":STR},["command"]),
f("start_dev_server","Start a local development server. Requires confirmation.",{"command":STR,"cwd":PATH},["command","cwd"]),
f("screenshot","Capture the screen.",{"path":PATH},[]),
f("system_info","Return basic CPU and memory information.",{},[]),
f("keyboard_write","Type text. Requires confirmation.",{"text":STR},["text"]),
f("mouse_click","Click a screen coordinate. Requires confirmation.",{"x":NUM,"y":NUM,"button":{"type":"string","enum":["left","right","middle"]}},["x","y"])
]
