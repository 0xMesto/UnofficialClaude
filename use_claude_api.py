from claude_api import UnofficialClaudeAPI

# The WebSocket endpoint of your running Chromium instance
BROWSER_WS_ENDPOINT = "ws://localhost:9222/devtools/browser/0ae2c38e-54c6-497c-b9dc-244ea216fda7"

try:
    with UnofficialClaudeAPI(BROWSER_WS_ENDPOINT) as api:
        api.start_conversation()
        
        response = api.send_message("hey can you help me")
        print("Claude's response:", response)
        
        # Send another message
        response = api.send_message("explain what quantum computing is ")
        print("Claude's response:", response)
          # Send another message
        response = api.send_message("thankyou ")
        print("Claude's response:", response)
        
        history = api.get_conversation_history()
        print("\nConversation History:")
        for message in history:
            print(f"{message['sender']}: {message['content']}")

except Exception as e:
    print(f"An error occurred: {e}")