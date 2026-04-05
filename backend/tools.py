import subprocess
from pathlib import Path
from langchain.tools import tool


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


def get_tools():
    return [read_file, write_file, list_directory, create_directory, run_terminal_command]
