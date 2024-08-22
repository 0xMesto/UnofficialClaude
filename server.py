import asyncio
import json
import time
import re
from typing import List, Optional, Union
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
from starlette.responses import StreamingResponse
from claude_api import Client as ClaudeClient
import logging
from sentence_transformers import SentenceTransformer
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
app = FastAPI(title="Claude-compatible OpenAI API")

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# You'll need to set these values appropriately
COOKIE =os.getenv('COOKIE')# Replace with actual cookie value
API_KEY = os.getenv('API_KEY')  # Set this to your desired API key

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

claude_client = None
embedding_model = None

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str = "claude-3-5-sonnet-20240620"
    messages: List[ChatMessage]
    max_tokens: Optional[int] = 20000
    temperature: Optional[float] = 0.7
    stream: Optional[bool] = False

class EmbeddingRequest(BaseModel):
    model: str
    input: Union[str, List[str]]

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header and api_key_header.startswith("Bearer "):
        key = api_key_header.split(" ")[1]
        if key == API_KEY:
            return key
    raise HTTPException(status_code=401, detail="Invalid or missing API Key")

@app.on_event("startup")
async def startup_event():
    global claude_client, embedding_model
    claude_client = ClaudeClient(COOKIE, model="claude-3-5-sonnet-20240620")
    logger.debug(f"Claude client initialized with organization ID: {claude_client.organization_id}")
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    logger.debug("Embedding model initialized")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/v1/models")
async def get_models(api_key: str = Depends(get_api_key)):
    if not claude_client:
        raise HTTPException(status_code=500, detail="Claude API not initialized")
    return {"data": claude_client.get_available_models()}

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest, api_key: str = Depends(get_api_key)):
    if not claude_client:
        raise HTTPException(status_code=500, detail="Claude API not initialized")

    try:
        claude_client.set_model(request.model)
        
        # Prepare the message for Claude
        claude_message = "\n".join([f"{msg.role}: {msg.content}" for msg in request.messages])

        # Create a new conversation
        logger.info("Creating new chat conversation")
        conversation = claude_client.create_new_chat()
        logger.debug(f"Create new chat response: {conversation}")
        conversation_id = conversation.get('uuid')
        if not conversation_id:
            logger.error(f"Failed to get conversation UUID. Full response: {conversation}")
            raise HTTPException(status_code=500, detail="Failed to create new conversation")

        # Send message
        logger.info(f"Sending message to conversation {conversation_id}")
        response = claude_client.send_message(claude_message, conversation_id)
        logger.debug(f"Received response: {response[:100]}...")  # Log first 100 chars of response

        if request.stream:
            return StreamingResponse(stream_claude_response(response, request), media_type="text/event-stream")
        else:
            return format_claude_response(response, request)
    except ValueError as e:
        logger.error(f"Invalid model specified: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"An error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def process_code_blocks(text):
    def replace_code_block(match):
        language = match.group(1) or ""
        code = match.group(2)
        return f"\n```{language}\n{code}\n```\n"

    # Replace code blocks
    text = re.sub(r'```(\w*)\n(.*?)\n```', replace_code_block, text, flags=re.DOTALL)
    
    # Ensure proper spacing around code blocks
    text = re.sub(r'(\n```[\w]*\n.*?\n```)\n?', r'\1\n\n', text, flags=re.DOTALL)
    
    return text

async def stream_claude_response(response: str, request: ChatCompletionRequest):
    processed_response = process_code_blocks(response)
    words = processed_response.split()
    
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

def format_claude_response(response: str, request: ChatCompletionRequest):
    processed_response = process_code_blocks(response)
    
    return {
        "id": f"chatcmpl-{int(time.time())}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": request.model,
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": processed_response,
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": sum(len(msg.content.split()) for msg in request.messages),
            "completion_tokens": len(processed_response.split()),
            "total_tokens": sum(len(msg.content.split()) for msg in request.messages) + len(processed_response.split())
        }
    }

@app.post("/v1/embeddings")
async def create_embedding(request: EmbeddingRequest, api_key: str = Depends(get_api_key)):
    if not embedding_model:
        raise HTTPException(status_code=500, detail="Embedding model not initialized")

    try:
        if isinstance(request.input, str):
            embeddings = embedding_model.encode([request.input]).tolist()
        else:
            embeddings = embedding_model.encode(request.input).tolist()

        return {
            "object": "list",
            "data": [
                {
                    "object": "embedding",
                    "embedding": embedding,
                    "index": i
                } for i, embedding in enumerate(embeddings)
            ],
            "model": request.model,
            "usage": {
                "prompt_tokens": sum(len(text.split()) for text in (request.input if isinstance(request.input, list) else [request.input])),
                "total_tokens": sum(len(text.split()) for text in (request.input if isinstance(request.input, list) else [request.input]))
            }
        }
    except Exception as e:
        logger.exception(f"An error occurred during embedding: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008)