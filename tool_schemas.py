def f(name, description, properties, required):
    return {"type":"function","name":name,"description":description,"parameters":{"type":"object","properties":properties,"required":required,"additionalProperties":False}}

STR={"type":"string"}
PATH={"type":"string"}
NUM={"type":"number"}

TOOL_SCHEMAS=[
f("open_app","Open a Windows application or executable.",{"app":STR},["app"]),
f("open_url","Open a URL in the default browser.",{"url":STR},["url"]),
f("list_files","List files and folders in an allowed directory.",{"path":PATH},["path"]),
f("find_files","Recursively find files using a glob pattern.",{"path":PATH,"pattern":STR},["path"]),
f("largest_files","Find the largest files in an allowed directory.",{"path":PATH,"count":{"type":"integer","minimum":1,"maximum":20}},["path"]),
f("create_folder","Create a folder inside an allowed root.",{"path":PATH},["path"]),
f("copy_file","Copy a file. Requires confirmation.",{"source":PATH,"destination":PATH},["source","destination"]),
f("move_file","Move a file. Requires confirmation.",{"source":PATH,"destination":PATH},["source","destination"]),
f("rename_file","Rename a file or folder. Requires confirmation.",{"path":PATH,"new_name":STR},["path","new_name"]),
f("delete_file","Send a file to the Windows Recycle Bin. Requires confirmation.",{"path":PATH},["path"]),
f("run_shell","Run a PowerShell command. Requires confirmation.",{"command":STR},["command"]),
f("screenshot","Capture the screen to a PNG file.",{"path":PATH},[]),
f("system_info","Return basic CPU and memory information.",{},[]),
f("keyboard_write","Type text using the keyboard. Requires confirmation.",{"text":STR},["text"]),
f("mouse_click","Click at a screen coordinate. Requires confirmation.",{"x":NUM,"y":NUM,"button":{"type":"string","enum":["left","right","middle"]}},["x","y"])
]
