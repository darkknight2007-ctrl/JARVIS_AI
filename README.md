# JARVIS — Local AI Web Dev Assistant

JARVIS is a fully local, agentic AI assistant for web development.  
It runs 100% on your machine using **Ollama** — no cloud, no API keys, complete privacy.

---

## Prerequisites

- **Python 3.10+** (`python3 --version`)
- **Ollama** installed — [ollama.com](https://ollama.com)

---

## Setup (One-time)

### 1. Pull the AI model

```bash
ollama pull qwen2.5-coder:7b
```

### 2. Install Python dependencies

```bash
cd "/Users/vishnu/Desktop/VS CODE/JARVIS/backend"
pip3 install -r requirements.txt
```

> **Note**: The project now uses langgraph for enhanced agent capabilities. Make sure all dependencies install correctly, especially langgraph.

---

## Running JARVIS (Startup Guide)

### 1. Start Ollama (if not already running)

```bash
ollama serve
```

### 2. Start the Backend Server

Whenever you open VS Code and want to wake JARVIS up, run this in a New Terminal:

```bash
cd "/Users/vishnu/Desktop/VS CODE/JARVIS/backend"
python3 main.py
```

### 3. Open the UI

Once the terminal says "Application startup complete", open your web browser and go to: 
**http://localhost:8000**

> **Note**: If you encounter any issues with the agent initialization, make sure you have the required models installed. The system now uses langgraph for enhanced agentic capabilities.

---

## How to Restart the Server

If JARVIS gets stuck, or if you see a **"Connection Refused"** error in your browser, it means the backend server crashed. To restart it:

1. Click inside the VS Code terminal where `python3 main.py` was running.
2. Press `Ctrl + C` on your keyboard to force-quit the stuck process.
3. Press the `Up Arrow` on your keyboard (this brings back the `python3 main.py` command) and hit `Enter`.
4. Hard Refresh your browser page (`Cmd+Shift+R` or `Ctrl+F5`)!

> **Troubleshooting Tip**: If you encounter agent initialization errors, check that all required dependencies are installed and that Ollama is running with the necessary models.

---

## Configuration
Edit `backend/.env` to change settings:
```
OLLAMA_MODEL=qwen2.5-coder:14b   # Change model here
OLLAMA_BASE_URL=http://localhost:11434
BACKEND_PORT=8000
```

---

## Project Structure
```
JARVIS/
├── backend/
│   ├── main.py          # FastAPI + WebSocket server
│   ├── agent.py         # LangGraph agent + JARVIS personality
│   ├── tools.py         # Agentic tools (file, terminal, etc.)
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── index.html       # Chat UI
│   ├── style.css        # Dark cyberpunk theme
│   └── app.js           # WebSocket client + streaming
└── README.md
```

> **Enhanced Capabilities**: The agent now uses langgraph for improved reasoning and tool execution patterns.

---

## What JARVIS Can Do
- 📁 **Read & write files** on your machine
- ⚡ **Run terminal commands** (npm, git, node, etc.)
- 🌐 **Build complete web projects** from scratch
- 🎨 **Generate HTML/CSS/JS** with modern best practices
- 🔧 **Debug and refactor** existing code
- 💬 **Remember conversation context** across messages
