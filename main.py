import json, os, sys
from pathlib import Path
from dotenv import load_dotenv
from agent import WindowsAgent

def main():
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        print("Missing OPENAI_API_KEY. Copy .env.example to .env and add your key.")
        sys.exit(1)
    config = json.loads(Path("config.json").read_text(encoding="utf-8"))
    agent = WindowsAgent(config)
    print("AI-Agent ready. Type a command, or 'exit' to quit.")
    while True:
        try:
            prompt = input("\nYou > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break
        if prompt.lower() in {"exit", "quit"}:
            break
        if prompt:
            try:
                print("\nAgent >", agent.run(prompt))
            except Exception as exc:
                print(f"\nAgent error: {exc}")

if __name__ == "__main__":
    main()
