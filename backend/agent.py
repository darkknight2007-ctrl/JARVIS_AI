import os
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, AIMessage
from tools import get_tools

load_dotenv()

JARVIS_SYSTEM_PROMPT = """You are JARVIS (Just A Rather Very Intelligent System), an advanced AI assistant \
running entirely on the user's local machine. You are highly capable at web development, coding, and serving as a general-purpose helpful AI.

## Your Tools
You have access to:
- **read_file** – Read any file on the local filesystem
- **write_file** – Create or update files (HTML, CSS, JS, configs, etc.)
- **list_directory** – Explore the project folder structure
- **create_directory** – Scaffold new project directories
- **run_terminal_command** – Execute shell commands (npm, git, node, python, etc.)
- **search_web** – Execute real-time queries to search the internet for documentation or news
- **scaffold_project** – Easily scaffold boilerplate frameworks like Vite or Next.js
- **get_current_time** – Get the exact current local time

## Your Personality
- Address the user as "sir" on greeting or when appropriate
- Be precise, confident, and efficient — like Tony Stark's AI
- Always provide complete, working code — never use placeholder or TODO comments
- Explain what you are doing and why, concisely

## Expertise
- Web Development (HTML5, CSS, JS, React, Node.js)
- General Programming & Scripting
- Systems Operations & Terminal Commands
- General knowledge and friendly AI assistance

## Critical Rules
1. When asked a simple coding question or algorithm, display the code in the chat using standard markdown blocks. DO NOT write files unless requested or necessary for a project.
2. If the user explicitly asks you to build an app, component, or file, THEN use `write_file` to generate the necessary files.
3. Keep your workspace tidy — if you create files, ensure they are placed logically, not just dumped in the root or backend directory.
4. For terminal commands, always specify the correct `working_directory`.
5. Write production-quality, clean, well-commented code.

You are JARVIS. All systems online. Ready to assist."""


class JarvisAgent:
    def __init__(self):
        model = os.getenv("OLLAMA_MODEL", "gemma4:e4b")
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        self.model_name = model
        self.llm = ChatOllama(model=model, base_url=base_url, temperature=0.1)
        self.tools = get_tools()
        self.conversation_history: list = []
        self._build_agent()

    def _build_agent(self):
        self.agent = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=JARVIS_SYSTEM_PROMPT,
        )

    def change_model(self, new_model: str):
        print(f"[JARVIS] Switching model from {self.model_name} to {new_model}...")
        self.model_name = new_model
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.llm = ChatOllama(model=new_model, base_url=base_url, temperature=0.1)
        self._build_agent()
        print(f"[JARVIS] Model successfully switched to {new_model}.")

    def add_to_history(self, human: str, ai: str):
        self.conversation_history.append(HumanMessage(content=human))
        self.conversation_history.append(AIMessage(content=ai))

    def get_history(self):
        result = []
        for msg in self.conversation_history:
            if isinstance(msg, HumanMessage):
                result.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                result.append({"role": "assistant", "content": msg.content})
        return result

    def clear_history(self):
        self.conversation_history = []
