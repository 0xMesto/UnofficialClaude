import os
import time
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from typing import List, Optional
from claude_api import UnofficialClaudeAPI
import uvicorn

app = FastAPI()

# Load the WebSocket endpoint from an environment variable for security
BROWSER_WS_ENDPOINT = os.getenv("BROWSER_WS_ENDPOINT")
if not BROWSER_WS_ENDPOINT:
    raise ValueError("BROWSER_WS_ENDPOINT environment variable is not set")

# Initialize the API
claude_api = UnofficialClaudeAPI(BROWSER_WS_ENDPOINT)

# Simple API key authentication
API_KEY = "your-secret-api-key"  # Replace with a secure key
api_key_header = APIKeyHeader(name="X-API-Key")

def get_api_key(api_key: str = Depends(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return api_key

class CompletionRequest(BaseModel):
    model: str
    prompt: str
    max_tokens: int = 100
    temperature: float = 0.7
    top_p: float = 1.0

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    max_tokens: int = 100
    temperature: float = 0.7
    top_p: float = 1.0

class EmbeddingRequest(BaseModel):
    model: str
    input: str

@app.post("/v1/completions")
async def create_completion(request: CompletionRequest, api_key: str = Depends(get_api_key)):
    try:
        with claude_api as api:
            api.start_conversation()
            api.set_model(request.model)
            response = api.send_message(request.prompt)
        
        return {
            "id": f"cmpl-{int(time.time())}",
            "object": "text_completion",
            "created": int(time.time()),
            "model": request.model,
            "choices": [
                {
                    "text": response,
                    "index": 0,
                    "logprobs": None,
                    "finish_reason": "length"
                }
            ],
            "usage": {
                "prompt_tokens": len(request.prompt.split()),
                "completion_tokens": len(response.split()),
                "total_tokens": len(request.prompt.split()) + len(response.split())
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/chat/completions")
async def create_chat_completion(request: ChatCompletionRequest, api_key: str = Depends(get_api_key)):
    try:
        with claude_api as api:
            api.start_conversation()
            api.set_model(request.model)
            
            # Combine all messages into a single prompt
            prompt = "\n".join([f"{msg.role}: {msg.content}" for msg in request.messages])
            response = api.send_message(prompt)
        
        return {
            "id": f"chatcmpl-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": request.model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": sum(len(msg.content.split()) for msg in request.messages),
                "completion_tokens": len(response.split()),
                "total_tokens": sum(len(msg.content.split()) for msg in request.messages) + len(response.split())
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/embeddings")
async def create_embedding(request: EmbeddingRequest, api_key: str = Depends(get_api_key)):
    # Note: This is a mock embedding endpoint. Claude doesn't provide embeddings.
    # You would need to implement your own embedding logic or use a different service.
    mock_embedding = [0.1] * 1536  # OpenAI's text-embedding-ada-002 uses 1536 dimensions
    return {
        "object": "list",
        "data": [
            {
                "object": "embedding",
                "embedding": mock_embedding,
                "index": 0
            }
        ],
        "model": request.model,
        "usage": {
            "prompt_tokens": len(request.input.split()),
            "total_tokens": len(request.input.split())
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)