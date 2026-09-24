# AI-Agent — Localhost Voice-Controlled Windows AI Agent

A local-first Windows personal AI agent with a browser control panel. Speak or type a command at localhost and the agent can use GPT plus local Windows tools to perform the task.

## What it can do
- Bangla or English voice commands from Chrome/Edge
- GPT multi-step tool-calling
- Create/edit software project files
- Open projects in VS Code
- Start local development servers
- Open browser previews and Windows apps
- Read/search/list files
- Copy, move, rename and send files to Recycle Bin
- PowerShell execution
- Screenshots
- Keyboard/mouse automation
- Browser confirmation UI for risky actions
- Local audit log in logs/agent.log
- Browser voice responses

## Requirements
- Windows 10/11
- Python 3.11+
- OpenAI API key
- Chrome or Edge recommended
- VS Code recommended; the `code` command should be available in PATH

## Install
Open PowerShell in the project folder:

```powershell
py -3 -m venv .venv
.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
```

Set:

```env
OPENAI_API_KEY=YOUR_API_KEY_HERE
OPENAI_MODEL=gpt-5.6
AGENT_HOST=127.0.0.1
AGENT_PORT=3000
```

Never commit `.env`.

## Run
```powershell
.venv\\Scripts\\Activate.ps1
python run_web.py
```

Open **http://127.0.0.1:3000** in Chrome or Edge and allow microphone access.

## Example voice commands
- “আমার Documents-এ একটা modern login page বানিয়ে দাও।”
- “এই project-টা VS Code-এ খুলে দাও।”
- “Development server চালিয়ে browser-এ দেখাও।”
- “Downloads-এর সবচেয়ে বড় ৫টা file দেখাও।”
- “Chrome খুলে YouTube-এ যাও।”
- “আমার project-এর npm error খুঁজে ঠিক করো।”
- “Desktop-এ Test নামে folder বানাও।”

For coding tasks the agent can inspect files, create multiple files, run commands, start a dev server, open VS Code and open a localhost preview as separate steps.

## Safety
The web UI asks for confirmation before file writes, shell commands, deletion, moves/copies/renames, simulated keyboard/mouse input and starting development servers. File operations are restricted to Desktop, Documents and Downloads by default.

This agent is intended for the user's own Windows machine. Do not use it to bypass access controls or access accounts/systems without authorization.

## Architecture
Browser voice UI → Local Flask server → GPT Responses API → Windows tools → VS Code / apps / files / terminal / browser.
