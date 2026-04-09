
# JARVIS — Local AI Web Dev Assistant

JARVIS is a fully local, agentic AI assistant for web development.  
It runs 100% on your machine using **Ollama** — no cloud, no API keys, complete privacy.

---

## 🛠 Prerequisites

- **Python 3.10+** (`python3 --version`)
- **Ollama** installed — [ollama.com](https://ollama.com)

---

## 🚀 Setup (One-time)

### 1. Pull the AI model

```bash
ollama pull qwen2.5-coder:7b
2. Install Python dependencies
Bash
cd backend
pip3 install -r requirements.txt
Note: This project utilizes LangGraph for enhanced agentic reasoning. Ensure all dependencies install correctly to enable full tool-calling capabilities.

🚦 Running JARVIS
1. Start Ollama
Ensure the Ollama service is active:

Bash
ollama serve
2. Start the Backend Server
Run the following in a new terminal window:

Bash
cd backend
python3 main.py
3. Open the UI
Once the terminal displays Application startup complete, navigate to:
http://localhost:8000

🔄 Troubleshooting & Restarts
If JARVIS becomes unresponsive or you see a "Connection Refused" error:

Stop the Process: Click the terminal running main.py and press Ctrl + C.

Restart: Press the Up Arrow key and hit Enter to run the start command again.

Refresh: Perform a Hard Refresh in your browser (Cmd+Shift+R or Ctrl+F5).

Tip: If initialization fails, verify that Ollama is running and that the model specified in your .env has been pulled.

⚙️ Configuration
Edit backend/.env to customize your setup:

Code snippet
OLLAMA_MODEL=qwen2.5-coder:7b
OLLAMA_BASE_URL=http://localhost:11434
BACKEND_PORT=8000
📂 Project Structure
Plaintext
JARVIS/
├── backend/
│   ├── main.py          # FastAPI + WebSocket server
│   ├── agent.py         # LangGraph agent logic
│   ├── tools.py         # File & terminal tools
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── index.html       # Chat UI
│   ├── style.css        # Dark cyberpunk theme
│   └── app.js           # WebSocket + streaming logic
└── README.md
✨ Features
📁 File System Access: Read and write files locally.

⚡ Terminal Integration: Execute commands (npm, git, node).

🌐 Full-Stack Generation: Build web projects from scratch.

🎨 Modern Styling: Generates clean HTML/CSS/JS.

🔧 Code Maintenance: Debug and refactor existing files.

💬 Context Awareness: Persistent conversation memory via LangGraph.


### Improvements made:
* **Path Portability**: Replaced `/Users/vishnu/Desktop/VS CODE/JARVIS/backend` with just `backend`. This allows the project to work regardless of where the folder is located or who is using it.
* **Visual Hierarchy**: Added emojis to headers (🛠, 🚀, 🚦) to make it more readable at a glance.
* **De-duplication**: You had three separate notes about LangGraph. I merged those into the "Setup" and "Features" sections to reduce clutter.
* **Consistency**: Standardized the code blocks (e.g., tagging the config block as `env` for better syntax highlighting).
