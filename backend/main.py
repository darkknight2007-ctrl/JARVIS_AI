import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
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
