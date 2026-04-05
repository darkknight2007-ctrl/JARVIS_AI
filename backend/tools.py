import subprocess
from datetime import datetime
from pathlib import Path
from langchain.tools import tool

try:
    from ddgs import DDGS
except ImportError:
    DDGS = None


@tool
def read_file(file_path: str) -> str:
    """Read the content of a file from the local filesystem.
    Use this to understand existing code or read project files.

    Args:
        file_path: The absolute or relative path to the file to read.
    """
    try:
        path = Path(file_path).expanduser().resolve()
        if not path.exists():
            return f"Error: File '{file_path}' does not exist."
        if not path.is_file():
            return f"Error: '{file_path}' is a directory, not a file."
        content = path.read_text(encoding="utf-8")
        return f"Content of `{file_path}`:\n\n```\n{content}\n```"
    except Exception as e:
        return f"Error reading file: {str(e)}"


@tool
def write_file(file_path: str, content: str) -> str:
    """Write content to a file. Creates the file and parent directories if they don't exist.
    Use this to create new files or update existing project files.

    Args:
        file_path: The absolute or relative path to write to.
        content: The complete content to write to the file.
    """
    try:
        path = Path(file_path).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return f"✅ Successfully created/updated '{file_path}' ({len(content)} characters written)."
    except Exception as e:
        return f"Error writing file: {str(e)}"


@tool
def list_directory(directory_path: str) -> str:
    """List all files and directories at the given path.
    Use this to explore project structure.

    Args:
        directory_path: The path to the directory to list.
    """
    try:
        path = Path(directory_path).expanduser().resolve()
        if not path.exists():
            return f"Error: Directory '{directory_path}' does not exist."
        if not path.is_dir():
            return f"Error: '{directory_path}' is a file, not a directory."
        items = []
        for item in sorted(path.iterdir()):
            if item.name.startswith("."):
                continue
            prefix = "📁" if item.is_dir() else "📄"
            size = f"  ({item.stat().st_size} bytes)" if item.is_file() else ""
            items.append(f"  {prefix} {item.name}{size}")
        if not items:
            return f"Directory '{directory_path}' is empty."
        return f"Contents of `{directory_path}`:\n" + "\n".join(items)
    except Exception as e:
        return f"Error listing directory: {str(e)}"


@tool
def create_directory(directory_path: str) -> str:
    """Create a new directory (and any parent directories) on the local filesystem.

    Args:
        directory_path: The path of the directory to create.
    """
    try:
        path = Path(directory_path).expanduser().resolve()
        path.mkdir(parents=True, exist_ok=True)
        return f"✅ Created directory: '{directory_path}'"
    except Exception as e:
        return f"Error creating directory: {str(e)}"


@tool
def run_terminal_command(command: str, working_directory: str = ".") -> str:
    """Execute a terminal/shell command on the local machine.
    Use this to run npm commands, git operations, start dev servers, install packages etc.
    SAFETY: Will not run destructive commands like rm -rf.

    Args:
        command: The shell command to execute.
        working_directory: The directory to run the command in. Defaults to current directory.
    """
    blocked = ["rm -rf /", "mkfs", ":(){ :|:& };:", "sudo rm -rf", "format c:"]
    for danger in blocked:
        if danger in command.lower():
            return f"❌ Blocked: Command contains forbidden pattern '{danger}'."
    try:
        work_dir = Path(working_directory).expanduser().resolve()
        if not work_dir.exists():
            return f"Error: Working directory '{working_directory}' does not exist."
        result = subprocess.run(
            command,
            shell=True,
            cwd=str(work_dir),
            capture_output=True,
            text=True,
            timeout=60,
        )
        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            output += f"\n[stderr]: {result.stderr}"
        if result.returncode != 0:
            output += f"\n[exit code: {result.returncode}]"
        return output.strip() if output.strip() else "✅ Command completed with no output."
    except subprocess.TimeoutExpired:
        return "❌ Error: Command timed out after 60 seconds."
    except Exception as e:
        return f"Error executing command: {str(e)}"


@tool
def get_current_time() -> str:
    """Get the current date and time.
    Use this to tell the user the time if they ask.
    """
    return f"The current date and time is: {datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}"

@tool
def search_web(query: str) -> str:
    """Search the internet for real-time information, news, programming documentation, or any external knowledge.
    Always use this when the user asks a question about current events or documentation you aren't sure about.
    """
    if DDGS is None:
        return "Error: duckduckgo-search is not installed."
        
    try:
        results = DDGS().text(query, max_results=3)
        if not results:
            return "No results found."
        
        output = []
        for r in results:
            output.append(f"Title: {r.get('title')}\nURL: {r.get('href')}\nSummary: {r.get('body')}\n")
        return "\n".join(output)
    except Exception as e:
        return f"Error searching the web: {str(e)}"

@tool
def scaffold_project(framework: str, path: str) -> str:
    """Scaffold a massive standard project in a given directory (e.g. React, Next.js, Vite).
    Arguments:
    - framework: The framework to scaffold. Valid options: 'vite', 'nextjs'.
    - path: The target directory (relative to current directory or absolute).
    """
    try:
        target_path = Path(path).resolve()
        
        if framework.lower() == 'vite':
            # Run npm create vite@latest
            cmd = f"npx -y create-vite@latest {target_path} --template react"
        elif framework.lower() == 'nextjs':
            cmd = f"npx -y create-next-app@latest {target_path} --typescript --tailwind --eslint --app --src-dir --import-alias '@/*'"
        else:
            return f"Error: Unsupported framework '{framework}'. Supported: vite, nextjs."
            
        # Ensure parent target path exists
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, text=True)
        return f"Successfully scaffolded {framework} project at {target_path}.\nTerminal Output:\n{output}"
    except subprocess.CalledProcessError as e:
        return f"Error scaffolding {framework} project: {e.output}"
    except Exception as e:
        return f"Error scaffolding project: {str(e)}"

def get_tools():
    return [read_file, write_file, list_directory, create_directory, run_terminal_command, get_current_time, search_web, scaffold_project]
