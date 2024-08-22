# Claude API Unofficial Client Setup Instructions

This guide will walk you through setting up and running the unofficial Claude API client. This client allows you to interact with Claude AI programmatically, similar to how you might use OpenAI's API.

## Purpose

This script provides a way to:
1. Interact with Claude AI through a Python API
2. Run a local server that mimics OpenAI's API structure but connects to Claude
3. Perform various tasks like chatting, generating embeddings, and managing conversations

## Prerequisites

* Python 3.7 or higher installed
* A Claude AI account
* Basic familiarity with command line operations

## Setup Instructions

### 1. Clone the Repository

First, clone the repository containing the Claude API scripts to your local machine.

```bash
git clone [repository_url]
cd [repository_name]
```

### 2. Set Up the Environment

Create a virtual environment and activate it:

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

Install the required packages:

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a file named `.env` in the root directory of the project. You'll need to fill this with several important values:

#### a. Get Your Organization ID

1. Log in to Claude AI in your web browser
2. In the same browser session, open a new tab and go to: https://api.claude.ai/api/organizations
3. You'll see a JSON response. Look for the `uuid` field of your desired organization
4. Copy this UUID

#### b. Get Your Session Cookie

1. While still on the Claude AI website, open your browser's developer tools (F12 or right-click and select "Inspect")
2. Go to the "Application" or "Storage" tab
3. Find the Cookies section and look for the `claude.ai` cookie
4. Copy the entire cookie string

#### c. Set Up the `.env` File

Open the `.env` file and add the following lines, replacing the placeholders with your actual values:

```bash
ORGANIZATION_ID=your_organization_uuid_here
COOKIE=your_full_cookie_string_here
API_KEY=your_chosen_api_key_here  # You can make this up; it's for your local API
```

### 4. Running the Scripts

#### a. Console Chat

To start a console-based chat with Claude:

```bash
python console_chat.py
```

This will allow you to interact with Claude directly in your terminal.

##### Video Showcase
*Add a link to a video demo of `console_chat.py` here.*

#### b. API Server

To run the local API server that mimics the OpenAI API structure:

```bash
python server.py
```

This will start a server on `http://localhost:8008`. You can now make API calls to this address as if it were the OpenAI API, but it will use Claude instead.

### 5. Using the API

With the server running, you can make requests to it using tools like `curl` or any programming language. Here's an example using Python's `requests` library:

```python
import requests

api_url = "http://localhost:8008/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {your_api_key_here}",
    "Content-Type": "application/json"
}
data = {
    "model": "claude-3-5-sonnet-20240620",
    "messages": [{"role": "user", "content": "Hello, Claude!"}]
}
response = requests.post(api_url, json=data, headers=headers)
print(response.json())
```

## Important Notes

* Keep your `.env` file secure and never share it publicly.
* The cookie and organization ID are sensitive. Only use them on trusted devices.
* This is an unofficial client. Be aware of Claude AI's terms of service when using it.
* The API mimics OpenAI's structure but may not be 100% compatible with all OpenAI API features.

## Troubleshooting

* If you encounter errors, double-check your cookie and organization ID.
* Ensure you're using the correct API key in your requests to the local server.
* Check the console output for any error messages when running the scripts.

## Disclaimer

This project is not affiliated with or endorsed by Claude AI. Use this client at your own risk, and make sure to comply with Claude AI's terms of service.

## Feedback and Contributions

If you encounter issues or have suggestions for improvements, please open an issue on the project's GitHub repository.