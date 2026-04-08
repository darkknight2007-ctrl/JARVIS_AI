import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from langchain_core.messages import HumanMessage

load_dotenv()

from agent import JarvisAgent

app = FastAPI(title="JARVIS API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the frontend
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")

jarvis = JarvisAgent()


@app.get("/")
async def serve_ui():
    index = frontend_path / "index.html"
    if index.exists():
        return HTMLResponse(index.read_text())
    return HTMLResponse("<h1>JARVIS backend is running. Place frontend files in /frontend.</h1>")


@app.get("/health")
async def health():
    return {"status": "online", "model": jarvis.model_name}


@app.get("/history")
async def get_history():
    return {"history": jarvis.get_history()}


@app.post("/clear")
async def clear_history():
    jarvis.clear_history()
    return {"status": "cleared"}

def get_dir_tree(directory: Path, ignore_dirs=None):
    if ignore_dirs is None:
        ignore_dirs = {".git", "node_modules", "venv", ".venv", "__pycache__"}
        
    tree = []
    try:
        paths = sorted(directory.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    except PermissionError:
        return []
        
    for path in paths:
        if path.name in ignore_dirs or path.name.startswith("."): # ignore hidden files & bloated dirs
            continue
            
        is_dir = path.is_dir()
        node = {
            "name": path.name,
            "path": str(path.absolute()),
            "type": "folder" if is_dir else "file",
        }
        if is_dir:
            node["children"] = get_dir_tree(path, ignore_dirs)
        tree.append(node)
    return tree

@app.get("/api/files")
async def get_files():
    # Return structure of the project root (parent of backend folder)
    root_path = Path(__file__).parent.parent.absolute()
    return {"tree": get_dir_tree(root_path)}

@app.get("/api/models")
async def get_models():
    """Fetch installed local models from Ollama."""
    import urllib.request
    import urllib.error
    
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    try:
        req = urllib.request.Request(f"{base_url}/api/tags", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            # Extract just the names
            models = [m.get("name") for m in data.get("models", [])]
            return {"models": models, "active": jarvis.model_name}
    except Exception as e:
        print(f"[ERROR] Failed to fetch Ollama models: {e}")
        return {"models": [jarvis.model_name], "active": jarvis.model_name}

@app.post("/api/model")
async def switch_model(request: Request):
    """Switch the current JARVIS LangChain engine model."""
    data = await request.json()
    new_model = data.get("model")
    if not new_model:
        return {"error": "No model provided"}, 400
        
    try:
        jarvis.change_model(new_model)
        return {"status": "success", "active": jarvis.model_name}
    except Exception as e:
        return {"error": str(e)}, 500


@app.post("/api/upload-image")
async def upload_image(file: UploadFile = File(...), question: str = Form("What's in this image?")):
    """Upload an image for vision analysis."""
    try:
        # Create uploads directory if it doesn't exist
        upload_dir = Path(__file__).parent / "uploads"
        upload_dir.mkdir(exist_ok=True)

        # Generate unique filename
        import uuid
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = upload_dir / unique_filename

        # Save the file
        contents = await file.read()
        file_path.write_bytes(contents)

        # Automatically analyze the image using the vision tool
        from tools import _analyze_image
        analysis_result = _analyze_image(str(file_path), question)

        return JSONResponse({
            "status": "success",
            "message": "Image uploaded and analyzed successfully",
            "file_path": str(file_path),
            "question": question,
            "analysis": analysis_result
        })

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/git/status")
async def git_status_api(directory: str = "."):
    """Get git status for a directory."""
    try:
        from tools import _git_status
        result = _git_status(directory)
        return {"status": "success", "output": result}
    except Exception as e:
        return {"error": str(e)}, 500


@app.post("/api/git/commit")
async def git_commit_api(request: Request):
    """Commit changes with a message."""
    try:
        data = await request.json()
        message = data.get("message")
        directory = data.get("directory", ".")

        if not message:
            return {"error": "Commit message is required"}, 400

        from tools import _git_commit
        result = _git_commit(message, directory)
        return {"status": "success", "output": result}
    except Exception as e:
        return {"error": str(e)}, 500


@app.post("/api/git/push")
async def git_push_api(request: Request):
    """Push changes to remote."""
    try:
        data = await request.json()
        directory = data.get("directory", ".")

        from tools import _git_push
        result = _git_push(directory)
        return {"status": "success", "output": result}
    except Exception as e:
        return {"error": str(e)}, 500


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("[JARVIS] WebSocket connected.")

    try:
        while True:
            raw = await websocket.receive_text()
            payload = json.loads(raw)
            user_message = payload.get("message", "").strip()

            if not user_message:
                continue

            print(f"[USER] {user_message}")

            try:
                # Build the message list: history + current message
                messages = list(jarvis.conversation_history) + [
                    HumanMessage(content=user_message)
                ]

                final_output = ""

                # Stream events from the LangGraph agent
                async for event in jarvis.agent.astream_events(
                    {"messages": messages},
                    version="v2",
                ):
                    kind = event["event"]

                    # Tool invocation started
                    if kind == "on_tool_start":
                        tool_name = event.get("name", "tool")
                        tool_input = str(event["data"].get("input", ""))[:300]
                        await websocket.send_json({
                            "type": "tool_start",
                            "tool": tool_name,
                            "input": tool_input,
                        })

                    # Tool invocation finished
                    elif kind == "on_tool_end":
                        tool_name = event.get("name", "tool")
                        tool_output = str(event["data"].get("output", ""))[:400]
                        await websocket.send_json({
                            "type": "tool_end",
                            "tool": tool_name,
                            "output": tool_output,
                        })

                    # Capture streamed LLM tokens
                    elif kind == "on_chat_model_stream":
                        chunk = event["data"].get("chunk")
                        if chunk and hasattr(chunk, "content") and chunk.content:
                            # Stream string chunks
                            if isinstance(chunk.content, str):
                                await websocket.send_json({
                                    "type": "token",
                                    "content": chunk.content,
                                })
                                final_output += chunk.content
                            # Stream dictionary blocks (some models output lists of text blocks)
                            elif isinstance(chunk.content, list):
                                for block in chunk.content:
                                    if isinstance(block, dict) and block.get("type") == "text":
                                        text_val = block.get("text", "")
                                        await websocket.send_json({
                                            "type": "token",
                                            "content": text_val,
                                        })
                                        final_output += text_val

                    # Fallback if streaming failed to catch it
                    elif kind == "on_chat_model_end":
                        output = event["data"].get("output")
                        if output and hasattr(output, "content") and isinstance(output.content, str):
                            if not final_output and output.content:
                                await websocket.send_json({
                                    "type": "token",
                                    "content": output.content,
                                })
                                final_output = output.content

                # Save to conversation history
                if final_output:
                    jarvis.add_to_history(user_message, final_output)

                # Signal completion
                await websocket.send_json({"type": "done"})
                print(f"[JARVIS] Response sent: {repr(final_output)}")

            except Exception as agent_err:
                print(f"[ERROR] Agent error: {agent_err}")
                import traceback
                traceback.print_exc()
                await websocket.send_json({
                    "type": "error",
                    "content": f"⚠️ An error occurred: {str(agent_err)}",
                })
                await websocket.send_json({"type": "done"})

    except WebSocketDisconnect:
        print("[JARVIS] WebSocket disconnected.")
    except Exception as e:
        print(f"[JARVIS] Fatal WebSocket error: {e}")


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    port = int(os.getenv("BACKEND_PORT", 8000))
    uvicorn.run("main:app", host=host, port=port, reload=True)
