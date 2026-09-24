# AI-Agent — GPT-Powered Windows Personal Assistant

A local-first Windows AI agent that turns natural-language commands into controlled computer actions.

## Features
- GPT tool-calling agent loop
- Windows app/process launching
- File search, copy, move, rename, Recycle Bin deletion
- PowerShell execution with confirmation
- Browser opening
- Screenshots
- Optional mouse/keyboard automation
- Optional microphone speech-to-text helper
- Local audit logging
- Permission/confirmation guardrails

## Requirements
- Windows 10/11
- Python 3.11+
- OpenAI API key

## Setup
```powershell
py -3 -m venv .venv
.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
python main.py
```

Set `OPENAI_API_KEY` in `.env`. Never commit `.env`.

## Example commands
- "Open Chrome"
- "Find the five largest files in Downloads"
- "Create a folder named Test on my Desktop"
- "Take a screenshot"
- "Open VS Code"
- "Run git status in my project folder"

Destructive actions, shell execution, and simulated input require confirmation by default.

## Safety
The default allowed filesystem roots are Desktop, Documents and Downloads. Expand them deliberately in `config.json` if needed. This agent is designed for the user's own Windows machine; do not use it to bypass access controls or access accounts without authorization.
