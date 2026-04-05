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

---

## Running JARVIS

### 1. Start Ollama (if not already running)
```bash
ollama serve
```

### 2. Start the backend
```bash
cd "/Users/vishnu/Desktop/VS CODE/JARVIS/backend"
python3 main.py
```

### 3. Open the UI
Open your browser and go to: **http://localhost:8000**

Or open `frontend/index.html` directly in your browser.

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
│   ├── agent.py         # LangChain agent + JARVIS personality
│   ├── tools.py         # Agentic tools (file, terminal, etc.)
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── index.html       # Chat UI
│   ├── style.css        # Dark cyberpunk theme
│   └── app.js           # WebSocket client + streaming
└── README.md
```

---

## What JARVIS Can Do
- 📁 **Read & write files** on your machine
- ⚡ **Run terminal commands** (npm, git, node, etc.)
- 🌐 **Build complete web projects** from scratch
- 🎨 **Generate HTML/CSS/JS** with modern best practices
- 🔧 **Debug and refactor** existing code
- 💬 **Remember conversation context** across messages
