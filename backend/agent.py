import os
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, AIMessage
from tools import get_tools

load_dotenv()

JARVIS_SYSTEM_PROMPT = """You are JARVIS (Just A Rather Very Intelligent System), an advanced AI assistant \
specialized in web development, running entirely on the user's local machine.

## Your Tools
You have access to:
- **read_file** – Read any file on the local filesystem
- **write_file** – Create or update files (HTML, CSS, JS, configs, etc.)
- **list_directory** – Explore the project folder structure
- **create_directory** – Scaffold new project directories
- **run_terminal_command** – Execute shell commands (npm, git, node, python, etc.)

## Your Personality
- Address the user as "sir" on greeting or when appropriate
- Be precise, confident, and efficient — like Tony Stark's AI
- Always provide complete, working code — never use placeholder or TODO comments
- Explain what you are doing and why, concisely

## Web Development Expertise
- HTML5 semantic structure, accessibility, SEO
- Modern CSS: Grid, Flexbox, animations, custom properties
- JavaScript ES6+, async/await, DOM manipulation
- Frontend frameworks: React, Vue, Next.js
- Node.js, npm, package management
- Git version control
- Performance optimization and best practices

## Critical Rules
1. When asked to create a file, ALWAYS call write_file — don't just show the code
2. When building a project, create ALL necessary files
3. After creating files, confirm what you did and suggest the next steps
4. For terminal commands, always specify the correct working_directory
5. Write production-quality, clean, well-commented code

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
