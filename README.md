# UnofficialClaude

This repository contains a Python wrapper for interacting with the Claude AI API, along with a FastAPI server that provides OpenAI-compatible endpoints for Claude's functionality.

## Components

1. **`claude_api.py`**: The main client for interacting with Claude AI.
2. **`console_chat.py`**: A simple console-based chat interface using the Claude API.
3. **`server.py`**: A FastAPI server that provides OpenAI-compatible endpoints for Claude.

## Features

- Interact with Claude AI using a Python client.
- Create and manage chat conversations.
- Upload attachments.
- Rename chat conversations.
- Simulate human-like behavior with randomized delays.
- OpenAI-compatible API endpoints for chat completions and embeddings.
- Simple console chat interface.
- Can be connected as an API with **AutoGen**, **Agent-zero**, **Perplexica**, or any other repository that supports integration with a local LLM.

## Installation

1. Clone this repository:

    ```bash
    git clone https://github.com/yourusername/claude-api-wrapper.git
    cd claude-api-wrapper
    ```

2. Install the required dependencies:

    ```bash
    pip install -r requirements.txt
    ```

## Usage

### Claude API Client

To use the Claude API client, you need to have a valid cookie for authentication:

```python
from claude_api import Client

cookie = "YOUR_COOKIE_HERE"
client = Client(cookie)

# Create a new chat
new_chat = client.create_new_chat()
conversation_id = new_chat['uuid']

# Send a message
response = client.send_message("Hello, Claude!", conversation_id)
print(response)
```
## Console Chat

To use the console chat interface:

1. Set your cookie in the `get_cookie()` function in `console_chat.py`.
2. Run the script:

    ```bash
    python console_chat.py
    ```

## FastAPI Server

To run the FastAPI server:

1. Set your cookie and desired API key in `server.py`.
2. Run the server:

    ```bash
    python server.py
    ```

The server will start on `http://localhost:8008`. You can then use the following endpoints:

- **GET** `/health`: Check server health.
- **GET** `/v1/models`: Get available Claude models.
- **POST** `/v1/chat/completions`: Create a chat completion.
- **POST** `/v1/embeddings`: Create embeddings.

## Configuration

- Set the `COOKIE` variable in `server.py` to your Claude AI cookie.
- Set the `API_KEY` variable in `server.py` to your desired API key for authentication.

## Notes

- This wrapper simulates human-like behavior by adding random delays between actions.
- The FastAPI server provides OpenAI-compatible endpoints, allowing you to use Claude with existing OpenAI-based applications.
- The embedding functionality uses the `sentence-transformers` library with the `all-MiniLM-L6-v2` model.
- The server can be connected as an API with tools such as **AutoGen**, **Agent-zero**, **Perplexica**, or any other repo that supports integration with local LLMs.

## Disclaimer

This project is not officially associated with Anthropic or OpenAI. Use it responsibly and in accordance with the terms of service of the respective AI providers.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open-source and available under the [MIT License](LICENSE).
