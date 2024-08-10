import asyncio
import json
import time
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
from starlette.responses import StreamingResponse
from claude_api import UnofficialClaudeAPI

app = FastAPI(title="Claude-compatible OpenAI API")

# You'll need to set these values appropriately
BROWSER_WS_ENDPOINT = "ws://localhost:9222/devtools/browser/aa8fd0fc-d262-4e5e-8136-f0176aeb73a8"
ORGANIZATION_ID = "05719259-a917-4a27-a78e-56ec78cc9b93"
API_KEY = "sk_claude_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"  # Set this to your desired API key

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

claude_api = None

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str = "Claude 3.5 Sonnet"
    messages: List[ChatMessage]
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.7
    stream: Optional[bool] = False

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header and api_key_header.startswith("Bearer "):
        key = api_key_header.split(" ")[1]
        if key == API_KEY:
            return key
    raise HTTPException(status_code=401, detail="Invalid or missing API Key")

@app.on_event("startup")
async def startup_event():
    global claude_api
    claude_api = await UnofficialClaudeAPI(BROWSER_WS_ENDPOINT, ORGANIZATION_ID).__aenter__()

@app.on_event("shutdown")
async def shutdown_event():
    if claude_api:
        await claude_api.close()

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest, api_key: str = Depends(get_api_key)):
    if not claude_api:
        raise HTTPException(status_code=500, detail="Claude API not initialized")

    # Prepare the message for Claude
    claude_message = "\n".join([f"{msg.role}: {msg.content}" for msg in request.messages])

    if request.stream:
        return StreamingResponse(stream_claude_response(claude_message, request), media_type="text/event-stream")

    # Non-streaming response
    try:
        response = await claude_api.send_message(claude_message, temperature=request.temperature, max_tokens=request.max_tokens)
        return format_claude_response(response, request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def stream_claude_response(message: str, request: ChatCompletionRequest):
    try:
        response = await claude_api.send_message(message, temperature=request.temperature, max_tokens=request.max_tokens)
        words = response.split()
        for i, word in enumerate(words):
            chunk = {
                "id": f"chatcmpl-{i}",
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": request.model,
                "choices": [{"delta": {"content": word + " "}, "index": 0, "finish_reason": None}],
            }
            yield f"data: {json.dumps(chunk)}\n\n"
            await asyncio.sleep(0.1)  # Simulate streaming delay
        
        # Send the final chunk
        final_chunk = {
            "id": f"chatcmpl-{len(words)}",
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": request.model,
            "choices": [{"delta": {}, "index": 0, "finish_reason": "stop"}],
        }
        yield f"data: {json.dumps(final_chunk)}\n\n"
        yield "data: [DONE]\n\n"
    except Exception as e:
        error_chunk = {
            "error": {
                "message": str(e),
                "type": "internal_error",
            }
        }
        yield f"data: {json.dumps(error_chunk)}\n\n"

def format_claude_response(response: str, request: ChatCompletionRequest):
    return {
        "id": f"chatcmpl-{int(time.time())}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": request.model,
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": response,
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": sum(len(msg.content.split()) for msg in request.messages),
            "completion_tokens": len(response.split()),
            "total_tokens": sum(len(msg.content.split()) for msg in request.messages) + len(response.split())
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)