import json, os
from openai import OpenAI
from tools import ToolExecutor, ConfirmationRequired

SYSTEM = """You are the user's local Windows personal AI agent.
Operate only on the user's own computer through provided tools.
Understand voice/text commands, plan multi-step work, execute tools, and report real results.
For coding tasks, inspect the project, make coherent changes, run appropriate checks, and open the result in VS Code and/or the local browser when useful.
Never claim success without tool confirmation. Do not expose secrets. Stay inside configured filesystem roots.
Potentially destructive, system-changing, shell, file mutation, and simulated-input actions require user confirmation.
Never bypass security controls or access accounts/systems without authorization.
"""

class WindowsAgent:
    def __init__(self, config):
        self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        self.model = os.getenv("OPENAI_MODEL", "gpt-5.6")
        self.executor = ToolExecutor(config)
        self.messages = [{"role": "system", "content": SYSTEM}]
        self.pending = None

    def _loop(self):
        for _ in range(16):
            response = self.client.responses.create(model=self.model, input=self.messages, tools=self.executor.schemas)
            items = getattr(response, "output", [])
            calls = [x for x in items if getattr(x, "type", "") == "function_call"]
            if not calls:
                answer = getattr(response, "output_text", "") or "Done."
                self.messages.append({"role": "assistant", "content": answer})
                return {"type": "answer", "answer": answer}
            self.messages.extend(items)
            for call in calls:
                args = json.loads(call.arguments or "{}")
                try:
                    result = self.executor.execute(call.name, args)
                except ConfirmationRequired as pending:
                    self.pending = {"call_id": call.call_id, "tool": call.name, "args": args, "message": pending.message}
                    return {"type":"confirmation_required","confirmation_required":True,"tool":call.name,"args":args,"message":pending.message}
                self.messages.append({"type":"function_call_output","call_id":call.call_id,"output":json.dumps(result,ensure_ascii=False)})
        return {"type":"answer","answer":"I stopped after the maximum number of tool steps. Continue with another command if needed."}

    def run(self, prompt):
        if self.pending:
            return {"type":"confirmation_required","confirmation_required":True,"tool":self.pending["tool"],"args":self.pending["args"],"message":self.pending["message"]}
        self.messages.append({"role":"user","content":prompt})
        return self._loop()

    def resolve_confirmation(self, approved):
        if not self.pending:
            return {"type":"answer","answer":"There is no pending confirmation."}
        pending=self.pending; self.pending=None
        result=self.executor.execute(pending["tool"],pending["args"],skip_confirmation=approved) if approved else {"ok":False,"cancelled":True,"message":"The user cancelled the action."}
        self.messages.append({"type":"function_call_output","call_id":pending["call_id"],"output":json.dumps(result,ensure_ascii=False)})
        return self._loop()
