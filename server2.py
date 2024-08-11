import asyncio
import json
import time
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
from starlette.responses import StreamingResponse
from claude_api import Client as ClaudeClient
import logging

app = FastAPI(title="Claude-compatible OpenAI API")

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# You'll need to set these values appropriately
COOKIE = "__stripe_mid=e9153cd4-5011-4cbd-af18-87e7e863b0620764fe; _gcl_au=1.1.1106054366.1718907813; _fbp=fb.1.1718907813879.324036528159443754; __ssid=1392ae80aa353d71067177c732b7aaa; intercom-device-id-lupk8zyo=9ed36bd1-07cd-4a87-a93f-e15210017630; lastActiveOrg=05719259-a917-4a27-a78e-56ec78cc9b93; _rdt_uuid=1711054816455.57490846-04aa-4c80-9cd7-3abed8a61969; sessionKey=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; CH-prefers-color-scheme=dark; activitySessionId=fefa5509-e15e-4c96-917c-edebfb093525; intercom-session-lupk8zyo=YitKaEpvQ2tYVzZaUmc1TkdreUdlb3dJOGhhK0d4TElnTzEzWFlCZk1qQkhOVzMwcDFFdVhSZ2xBV0tITjluYy0tclpYMXhCd0wzZUxMMmZXTmgxenBoUT09--f8dd73e738a923e55418ee466eb8db2e65e2ae2f; cf_clearance=v4yfJ.FbyyL9DbyHCUp.PWRdYVXT_TCDN4c_qfg3DeQ-1723289344-1.0.1.1-GcWjL1jPhzewemoA00ImP1B4jpwQmqZ.AQYTOXqntWRMOb.ZZbr3nvd_vlhZmREHpiBSTx3Etlxi.4txZS0TiQ; __cf_bm=9tAgxyONmRAiB5Lxy0lgQD5w8fianrV1AKB.twiEbao-1723290534-1.0.1.1-CVFQrHVwgbcNrMjVSedVemjvrsfZZt4OU3GcA2O1CjijWZO4E18ft4UT1vDMUb8po6J.ABjCreMedv56ZS5.QQ"
API_KEY = "sk_claude_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"  # Set this to your desired API key

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

claude_client = None

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str = "claude-3-5-sonnet-20240620"
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
    global claude_client
    claude_client = ClaudeClient(COOKIE)

async def handle_rate_limit(reset_time):
    wait_time = reset_time - time.time() + 5400  # 1.5 hours (5400 seconds) after reset time
    if wait_time > 0:
        logger.info(f"Rate limit exceeded. Waiting for {wait_time/3600:.2f} hours before retrying.")
        await asyncio.sleep(wait_time)
    else:
        logger.info("Rate limit reset time has already passed. Retrying immediately.")

async def send_message_with_retry(claude_message, conversation_id, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = claude_client.send_message(claude_message, conversation_id)
            return response
        except Exception as e:
            error_message = str(e)
            if "rate_limit_error" in error_message:
                try:
                    error_data = json.loads(json.loads(error_message)['error']['message'])
                    reset_time = error_data.get('resetsAt')
                    if reset_time:
                        await handle_rate_limit(reset_time)
                    else:
                        logger.error("Rate limit error without reset time. Retrying after 1 hour.")
                        await asyncio.sleep(3600)
                except json.JSONDecodeError:
                    logger.error("Failed to parse rate limit error message. Retrying after 1 hour.")
                    await asyncio.sleep(3600)
            else:
                logger.error(f"Error sending message: {error_message}")
                if attempt == max_retries - 1:
                    raise

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest, api_key: str = Depends(get_api_key)):
    if not claude_client:
        raise HTTPException(status_code=500, detail="Claude API not initialized")

    # Prepare the message for Claude
    claude_message = "\n".join([f"{msg.role}: {msg.content}" for msg in request.messages])

    # Create a new conversation
    conversation = claude_client.create_new_chat()
    conversation_id = conversation['uuid']

    if request.stream:
        return StreamingResponse(stream_claude_response(claude_message, conversation_id, request), media_type="text/event-stream")
    
    # Non-streaming response
    try:
        response = await send_message_with_retry(claude_message, conversation_id)
        return format_claude_response(response, request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def stream_claude_response(message: str, conversation_id: str, request: ChatCompletionRequest):
    try:
        response = await send_message_with_retry(message, conversation_id)
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
    uvicorn.run(app, host="0.0.0.0", port=8008)