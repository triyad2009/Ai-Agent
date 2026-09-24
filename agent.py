import json, os
from openai import OpenAI
from tools import ToolExecutor
from tool_schemas import TOOL_SCHEMAS

SYSTEM = """You are a careful Windows personal AI assistant.
Use tools to accomplish the user's requested computer tasks.
Be concise and report actual tool results. Never claim success without a successful tool result.
Ask for confirmation whenever the tool returns cancelled/confirmation-required.
Do not expose API keys, passwords, tokens, cookies, or other secrets.
Prefer reversible actions and stay within configured filesystem roots.
Never bypass security controls or access systems/accounts without authorization.
"""

class WindowsAgent:
    def __init__(self, config):
        self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        self.model = os.getenv("OPENAI_MODEL", "gpt-5.6")
        self.executor = ToolExecutor(config)
        self.messages = [{"role": "system", "content": SYSTEM}]

    def run(self, prompt):
        self.messages.append({"role": "user", "content": prompt})
        for _ in range(12):
            response = self.client.responses.create(
                model=self.model,
                input=self.messages,
                tools=TOOL_SCHEMAS,
            )
            items = getattr(response, "output", [])
            calls = [x for x in items if getattr(x, "type", "") == "function_call"]
            if not calls:
                answer = getattr(response, "output_text", "") or "Done."
                self.messages.append({"role": "assistant", "content": answer})
                return answer
            self.messages.extend(items)
            for call in calls:
                args = json.loads(call.arguments or "{}")
                result = self.executor.execute(call.name, args)
                self.messages.append({
                    "type": "function_call_output",
                    "call_id": call.call_id,
                    "output": json.dumps(result, ensure_ascii=False)
                })
        return "Stopped after the maximum tool steps."
