import os
import logging
from claude_api import Client
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_cookie():
    cookie = os.getenv('COOKIE')
    if not cookie:
        raise ValueError("Please set the 'cookie' variable.")
    logger.debug(f"Cookie retrieved: {cookie[:20]}...") # Log first 20 chars of cookie
    return cookie

def main():
    try:
        cookie = get_cookie()
        logger.info("Initializing Claude client")
        claude = Client(cookie)
        logger.debug(f"Claude client initialized with organization ID: {claude.organization_id}")
        conversation_id = None

        print("Welcome to Claude AI Chat!")

        while True:
            user_input = input("You: ")

            if user_input.lower() == 'exit':
                print("Thank you!")
                break

            if not conversation_id:
                logger.info("Creating new chat conversation")
                conversation = claude.create_new_chat()
                logger.debug(f"Create new chat response: {conversation}")
                conversation_id = conversation.get('uuid') if conversation else None
                if not conversation_id:
                    logger.error(f"Failed to get conversation UUID. Full response: {conversation}")
                    raise ValueError("Unable to create new conversation")

            logger.info(f"Sending message to conversation {conversation_id}")
            response = claude.send_message(user_input, conversation_id)
            logger.debug(f"Received response: {response[:100]}...") # Log first 100 chars of response
            print("Chatbot:", response)

    except Exception as e:
        logger.exception(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
